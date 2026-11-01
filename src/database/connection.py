
import os
import psycopg2

from src.utils.logger import setup_logger

logger = setup_logger()


def conectar():
    conexao = None

    senha_banco = os.environ.get("DB_PASSWORD")

    if not senha_banco:
        logger.error(
            "Variável de ambiente DB_PASSWORD não configurada."
        )
        return None

    try:
        conexao = psycopg2.connect(
            host="localhost",
            port=5432,
            database="tcc_libras",
            user="postgres",
            password=senha_banco
        )

        logger.info("Conexão com o banco estabelecida.")

        return conexao

    except Exception as erro:
        logger.error(
            f"Erro ao conectar ao banco: {erro}"
        )

        return None
