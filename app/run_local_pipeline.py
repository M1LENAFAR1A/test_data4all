import io
import logging
import os
import urllib.parse
from pathlib import Path

import pandas as pd

from app.connectors.minio import MinioConnector
from app.core.config import settings
from app.schemas.response import MinioResponse, Response
from app.utils.date import processar_csv

# Arquivo de taxonomia (deve conter as colunas 'original' e 'taxonomy')
TAXONOMY_FILE = settings.TAXONOMY_FILE


class TransformationPipeline:
    def __init__(self, output_folder, minio_connector: MinioConnector):
        self.output_folder = output_folder.rstrip("/") + "/"  # garante que termina com '/'
        self.minio_connector = minio_connector
        self.logger = logging.getLogger('app')

    def create_transformation_directory(self):
        os.makedirs(self.output_folder, exist_ok=True)

    def run(self, file_path: str) -> tuple[bool, str]:
        self.logger.info(' [*] Starting pipeline...')
        self.logger.info('Applying date and coordinates transformations')
        date_transformation_response: Response = self.date_transformation(file_path=file_path)
        if date_transformation_response.success:
            self.logger.info("Date transformation successful. Output file: %s", date_transformation_response.value)
            self.logger.info("Applying taxonomy transformation")
            new_filename = date_transformation_response.value
            taxonomy_transformation_response = self.taxonomy_transformation(new_filename=new_filename)
            if not taxonomy_transformation_response.success:
                os.remove(urllib.parse.urljoin(self.output_folder, new_filename))
                return False, taxonomy_transformation_response.value

            self.logger.info("Taxonomy transformation successful. Output file: %s", taxonomy_transformation_response.value)
            self.logger.info("Inserting transformed value into Minio")
            transformed_basename = taxonomy_transformation_response.value.split("/")[-1]
            self.insert_file_into_minio(
                file_path=taxonomy_transformation_response.value,
                new_filename=f'/transformed/{transformed_basename}'
            )
            # Remove o arquivo intermediário da transformação de data
            try:
                os.remove(urllib.parse.urljoin(self.output_folder, new_filename))
            except Exception as e:
                self.logger.warning("Could not remove intermediate file: %s", e)
            # Verifica e envia arquivo de espécies ausentes, se existir
            missing_species_path = urllib.parse.urljoin(self.output_folder, 'missing_species.csv')
            if os.path.exists(missing_species_path):
                self.logger.info('Inserting missing species into data lake')
                self.insert_file_into_minio(
                    file_path=missing_species_path,
                    new_filename='/missing/missing_species.csv'
                )
                os.remove(missing_species_path)
            return True, taxonomy_transformation_response.value
        else:
            self.logger.error("Something went wrong in the transformation")
            self.logger.error(f"{date_transformation_response.value}")
            self.logger.info("Inserting again in the queue")
            return False, date_transformation_response.value

    def date_transformation(self, file_path: str) -> Response:
        object_response: MinioResponse = self.minio_connector.get_object(file_path=file_path)
        if object_response.success:
            try:
                df = pd.read_csv(io.BytesIO(object_response.value))
            except Exception as e:
                self.logger.error("Error reading CSV from Minio: %s", e)
                return Response(success=False, value=f"Error reading CSV: {e}")
            # processar_csv deve processar o DataFrame e salvar o arquivo transformado no output_folder
            processing_response = processar_csv(df=df, file_path=file_path, output_folder=self.output_folder)
            self.logger.info("processar_csv returned: %s", processing_response)
            return Response(success=True, value=processing_response)
        else:
            return Response(success=False, value=object_response.value)

    def taxonomy_transformation(self, new_filename: str) -> Response:
        # Constrói o caminho completo do arquivo transformado pela data
        transformed_file_path = os.path.join(self.output_folder, new_filename)
        self.logger.info("Reading file for taxonomy transformation: %s", transformed_file_path)
        try:
            # Ajuste o separador e encoding conforme o formato do seu CSV
            df = pd.read_csv(transformed_file_path, sep=';', encoding='utf-8')
        except Exception as e:
            self.logger.error("Error reading transformed CSV for taxonomy transformation", exc_info=True)
            return Response(success=False, value=f"Error reading transformed CSV: {e}")
        try:
            taxonomy_df = pd.read_csv(TAXONOMY_FILE, sep=';', encoding='utf-8')
            mapping = dict(zip(taxonomy_df['original'], taxonomy_df['taxonomy']))
        except Exception as e:
            self.logger.error("Error reading taxonomy file", exc_info=True)
            return Response(success=False, value=f"Error reading taxonomy file: {e}")
        
        if 'species' in df.columns:
            self.logger.info("Applying taxonomy mapping to 'species' column")
            df['species'] = df['species'].map(mapping).fillna(df['species'])
        else:
            self.logger.warning("No 'species' column found for taxonomy transformation.")
        
        taxonomy_transformed_filename = f"taxonomy_transformed_{os.path.basename(new_filename)}"
        taxonomy_transformed_file = os.path.join(self.output_folder, taxonomy_transformed_filename)
        try:
            df.to_csv(taxonomy_transformed_file, index=False, sep=';')
            self.logger.info("Taxonomy transformed CSV saved to: %s", taxonomy_transformed_file)
        except Exception as e:
            self.logger.error("Error saving taxonomy transformed CSV", exc_info=True)
            return Response(success=False, value=f"Error saving taxonomy transformed CSV: {e}")
        
        return Response(success=True, value=taxonomy_transformed_file)

    def insert_file_into_minio(self, file_path: str, new_filename: str):
        csv_path = Path(file_path)
        if csv_path.exists():
            csv_size = os.stat(csv_path).st_size
            with open(csv_path, 'rb') as csv:
                self.minio_connector.upload_data(
                    file_path=f'{new_filename}',
                    data=csv,
                    content_type='text/csv',
                    file_size=csv_size
                )
            self.logger.info("File inserted into Minio: %s", new_filename)
