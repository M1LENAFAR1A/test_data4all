# arquivo: run_local_pipeline.py
import logging

# Importe o pipeline original e o nosso "mock" local
from connectors.local_minio_connector import LocalMinioConnector
from models.transformation_pipeline import TransformationPipeline  # <-- Ajuste se seu arquivo tiver outro nome/path

logging.basicConfig(level=logging.INFO)

def main():
    # 1. Instancia o conector local, apontando para onde estão seus CSVs
    local_connector = LocalMinioConnector(base_folder="app/static")

    # 2. Define a pasta de saída (pode ser "app/static" ou "app/static/transformados" etc.)
    output_folder = "app/static"

    # 3. Instancia o pipeline com esse conector
    pipeline = TransformationPipeline(
        output_folder=output_folder,
        minio_connector=local_connector
    )

    # 4. Nome do CSV bruto que você copiou manualmente para "app/static"
    raw_file = "dados_brutos.csv"

    # 5. Executa o pipeline
    success, result = pipeline.run(file_path=raw_file)

    if success:
        print("Transformação concluída com sucesso!")
        print(f"Arquivo final: {result}")
    else:
        print("Houve erro na transformação.")
        print(f"Mensagem de erro: {result}")

if __name__ == "__main__":
    main()
