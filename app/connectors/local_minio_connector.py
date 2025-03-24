# arquivo: local_minio_connector.py
import os
from schemas.response import MinioResponse

class LocalMinioConnector:
    """
    Este conector simula o comportamento do MinioConnector,
    mas lê e grava arquivos na pasta local (ex: app/static).
    """
    def __init__(self, base_folder="app/static"):
        self.base_folder = base_folder

    def get_object(self, file_path: str) -> MinioResponse:
        """
        Em vez de baixar o objeto do Minio, vamos ler o arquivo localmente.
        """
        import io

        full_path = os.path.join(self.base_folder, file_path)
        if not os.path.exists(full_path):
            return MinioResponse(success=False, value=f"Arquivo não encontrado: {full_path}")

        try:
            with open(full_path, 'rb') as f:
                data = f.read()
            return MinioResponse(success=True, value=data)
        except Exception as e:
            return MinioResponse(success=False, value=str(e))

    def upload_data(self, file_path: str, data, content_type: str, file_size: int):
        """
        Em vez de fazer upload no Minio, vamos salvar localmente.
        """
        import io
        # Remover barra inicial (se existir) para não criar subpastas estranhas
        file_path = file_path.lstrip("/")

        full_path = os.path.join(self.base_folder, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # 'data' é um arquivo aberto em modo binário, então escrevemos direto
        with open(full_path, 'wb') as f:
            f.write(data.read())

        # Volta o cursor para o início, se precisar ler novamente
        data.seek(0)

        return MinioResponse(success=True, value=f"Arquivo salvo localmente em {full_path}")
