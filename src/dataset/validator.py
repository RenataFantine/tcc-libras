import csv
import os
import math

from src.utils.logger import setup_logger
from src.dataset.config import (
    DATASET_PATH,
    SIGNAL_NAME,
    FRAMES_PER_SEQUENCE
)

logger = setup_logger()

EXPECTED_COLUMNS = 64


def validar_arquivo(caminho):
    """
    Valida um arquivo CSV de uma sequência.
    """

    erros = []

    try:

        with open(
            caminho,
            mode="r",
            newline="",
            encoding="utf-8"
        ) as arquivo:

            reader = csv.reader(arquivo)

            linhas = list(reader)

        # -------------------------------------------------
        # Verifica se existe conteúdo
        # -------------------------------------------------

        if not linhas:

            erros.append("Arquivo vazio.")
            return erros

        cabecalho = linhas[0]
        dados = linhas[1:]

        # -------------------------------------------------
        # Verifica quantidade de colunas
        # -------------------------------------------------

        if len(cabecalho) != EXPECTED_COLUMNS:

            erros.append(
                f"Cabeçalho possui {len(cabecalho)} "
                f"colunas. Esperado: {EXPECTED_COLUMNS}."
            )

        # -------------------------------------------------
        # Verifica quantidade de frames
        # -------------------------------------------------

        if len(dados) != FRAMES_PER_SEQUENCE:

            erros.append(
                f"Possui {len(dados)} frames. "
                f"Esperado: {FRAMES_PER_SEQUENCE}."
            )

        # -------------------------------------------------
        # Verifica cada frame
        # -------------------------------------------------

        for indice, linha in enumerate(
            dados,
            start=1
        ):

            if len(linha) != EXPECTED_COLUMNS:

                erros.append(
                    f"Frame {indice}: possui "
                    f"{len(linha)} colunas. "
                    f"Esperado: {EXPECTED_COLUMNS}."
                )

                continue

            # Verifica número do frame
            try:

                numero_frame = int(linha[0])

                if numero_frame != indice:

                    erros.append(
                        f"Frame {indice}: "
                        f"número incorreto "
                        f"({numero_frame})."
                    )

            except ValueError:

                erros.append(
                    f"Frame {indice}: "
                    f"número de frame inválido."
                )

            # Verifica coordenadas
            for coluna, valor in enumerate(
                linha[1:],
                start=1
            ):

                if valor == "":

                    erros.append(
                        f"Frame {indice}, "
                        f"coluna {coluna}: "
                        f"valor vazio."
                    )

                    continue

                try:

                    numero = float(valor)

                    if not math.isfinite(numero):

                        erros.append(
                            f"Frame {indice}, "
                            f"coluna {coluna}: "
                            f"valor inválido."
                        )

                except ValueError:

                    erros.append(
                        f"Frame {indice}, "
                        f"coluna {coluna}: "
                        f"não é numérico."
                    )

    except Exception as erro:

        erros.append(
            f"Erro ao ler arquivo: {erro}"
        )

    return erros


def validar_dataset():

    pasta = os.path.join(
        DATASET_PATH,
        SIGNAL_NAME
    )

    if not os.path.exists(pasta):

        logger.error(
            f"Pasta não encontrada: {pasta}"
        )

        return

    arquivos = sorted(
        arquivo
        for arquivo in os.listdir(pasta)
        if arquivo.endswith(".csv")
    )

    if not arquivos:

        logger.warning(
            "Nenhum arquivo CSV encontrado."
        )

        return

    print("\n" + "=" * 50)
    print("VALIDAÇÃO DO DATASET")
    print("=" * 50)

    total = len(arquivos)
    aprovados = 0
    reprovados = 0

    for arquivo in arquivos:

        caminho = os.path.join(
            pasta,
            arquivo
        )

        erros = validar_arquivo(caminho)

        if not erros:

            print(
                f"✅ {arquivo} - OK"
            )

            aprovados += 1

        else:

            print(
                f"❌ {arquivo} - ERROS"
            )

            for erro in erros:

                print(
                    f"   └── {erro}"
                )

            reprovados += 1

    print("\n" + "-" * 50)

    print(
        f"Total: {total}"
    )

    print(
        f"Aprovados: {aprovados}"
    )

    print(
        f"Reprovados: {reprovados}"
    )

    print("-" * 50)

    if reprovados == 0:

        print(
            "🎉 DATASET VALIDADO COM SUCESSO!"
        )

    else:

        print(
            "⚠️ Existem arquivos que precisam "
            "ser corrigidos."
        )

    print("=" * 50 + "\n")


if __name__ == "__main__":
    validar_dataset()