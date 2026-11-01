import csv
import os

from src.dataset.config import DATASET_PATH, SIGNAL_NAME


def testar_csv():

    caminho = os.path.join(
        DATASET_PATH,
        SIGNAL_NAME,
        "001.csv"
    )

    if not os.path.exists(caminho):

        print("❌ Arquivo não encontrado:")
        print(caminho)
        return

    with open(
        caminho,
        mode="r",
        encoding="utf-8"
    ) as arquivo:

        leitor = csv.reader(arquivo)

        cabecalho = next(leitor)
        primeira_linha = next(leitor)

    print("=" * 60)
    print(" TESTE DO CSV")
    print("=" * 60)

    print()
    print(f"Colunas encontradas: {len(cabecalho)}")
    print(f"Valores na primeira linha: {len(primeira_linha)}")

    # -----------------------------------------------------
    # ESTRUTURA
    # -----------------------------------------------------

    if len(cabecalho) == 127:

        print("✅ Cabeçalho possui 127 colunas.")

    else:

        print(
            f"❌ Cabeçalho incorreto. "
            f"Esperado: 127 | "
            f"Encontrado: {len(cabecalho)}"
        )

    if len(primeira_linha) == 127:

        print("✅ Linha possui 127 valores.")

    else:

        print(
            f"❌ Linha incorreta. "
            f"Esperado: 127 | "
            f"Encontrado: {len(primeira_linha)}"
        )

    # -----------------------------------------------------
    # SEPARA AS MÃOS
    # -----------------------------------------------------

    left_values = primeira_linha[1:64]
    right_values = primeira_linha[64:127]

    left_nonzero = sum(
        float(valor) != 0
        for valor in left_values
    )

    right_nonzero = sum(
        float(valor) != 0
        for valor in right_values
    )

    print()
    print("MÃO ESQUERDA")
    print(
        f"Valores diferentes de zero: "
        f"{left_nonzero}/63"
    )

    print()
    print("MÃO DIREITA")
    print(
        f"Valores diferentes de zero: "
        f"{right_nonzero}/63"
    )

    # -----------------------------------------------------
    # RESULTADO
    # -----------------------------------------------------

    print()
    print("=" * 60)

    if left_nonzero > 0 and right_nonzero > 0:

        print(
            "🎉 DUAS MÃOS ESTÃO SENDO SALVAS!"
        )

    elif left_nonzero > 0:

        print(
            "🖐️ Apenas a mão esquerda possui dados."
        )

    elif right_nonzero > 0:

        print(
            "🖐️ Apenas a mão direita possui dados."
        )

    else:

        print(
            "❌ NENHUMA MÃO POSSUI DADOS."
        )

    print("=" * 60)


if __name__ == "__main__":
    testar_csv()