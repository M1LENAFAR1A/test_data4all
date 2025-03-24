import io
import logging
import pandas as pd
import chardet
from app.schemas.response import Response  # Certifique-se de que este módulo esteja definido

class TransformationPipeline:
    def __init__(self, output_folder, minio_connector):
        self.output_folder = output_folder
        self.minio_connector = minio_connector

    def run(self, file_path: str):
        logging.info("Starting transformation pipeline...")
        logging.info("Applying date and coordinates transformations")
        success, result = self.date_transformation(file_path=file_path)
        return success, result

    def date_transformation(self, file_path: str) -> Response:
        # Obtém o arquivo (em bytes) através do conector
        object_response = self.minio_connector.get_object(file_path)
        
        # Detecta a codificação do conteúdo do CSV usando chardet
        detected = chardet.detect(object_response.value)
        encoding = detected['encoding']
        logging.info(f"Detected encoding: {encoding}")
        
        try:
            # Lê o CSV utilizando o delimitador adequado (ajuste o sep se necessário)
            df = pd.read_csv(io.BytesIO(object_response.value), encoding=encoding, sep=';')
        except Exception as e:
            logging.error("Error reading CSV file", exc_info=True)
            return False, f"Error reading CSV: {e}"
        
        # Exemplo de transformação: converte a coluna 'date' para datetime, se existir
        if 'date' in df.columns:
            try:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            except Exception as e:
                logging.error("Error transforming 'date' column", exc_info=True)
                return False, f"Error transforming 'date' column: {e}"
        
        # Salva o DataFrame transformado em um novo arquivo CSV
        output_file = f"{self.output_folder}/transformed.csv"
        try:
            df.to_csv(output_file, index=False)
        except Exception as e:
            logging.error("Error saving transformed CSV", exc_info=True)
            return False, f"Error saving transformed CSV: {e}"
        
        # Retorna um objeto Response contendo o caminho do arquivo final
        response = Response(success=True, value=output_file)
        return True, response

