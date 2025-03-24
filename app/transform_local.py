# Arquivo: transform_local.py

import pandas as pd
import os

def transformar_dados_brutos():
    """
    Lê o CSV bruto, faz alguma transformação simples e salva em um CSV transformado.
    """
    # Caminho até o CSV bruto (ajustar se necessário)
    caminho_bruto = os.path.join("static", "dados_brutos.csv")
    # Caminho onde o CSV final será salvo
    caminho_transformado = os.path.join("static", "dados_transformados.csv")

    # 1. Ler o CSV bruto
    df = pd.read_csv(caminho_bruto)

    # 2. Exemplo de transformação simples:
    #    (a) Renomear colunas
    #    (b) Criar uma nova coluna
    #    (c) Filtrar linhas etc.
    # Aqui, como exemplo, vamos só criar uma nova coluna 'exemplo' com valor fixo "transformado"
    df["exemplo"] = "transformado"

    # 3. Salvar no CSV transformado
    df.to_csv(caminho_transformado, index=False, encoding="utf-8")

    print(f"Transformação concluída! Arquivo salvo em: {caminho_transformado}")

if __name__ == "__main__":
    transformar_dados_brutos()
