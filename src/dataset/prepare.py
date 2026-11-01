import numpy as np

from sklearn.model_selection import train_test_split

from src.dataset.loader import carregar_dataset
from src.utils.logger import setup_logger


logger = setup_logger()


def preparar_dataset():
    """
    Carrega o dataset e realiza a divisão
    entre treinamento e teste.

    Retorna:

        X_train:
            Dados utilizados no treinamento.

        X_test:
            Dados utilizados no teste.

        y_train:
            Classes correspondentes ao treinamento.

        y_test:
            Classes correspondentes ao teste.

        nomes_classes:
            Nome das classes do dataset.
    """

    # =====================================================
    # CARREGAMENTO
    # =====================================================

    X, y, nomes_classes = (
        carregar_dataset()
    )

    if len(X) == 0:

        logger.error(
            "Nenhum dado disponível "
            "para preparação."
        )

        return (
            None,
            None,
            None,
            None,
            []
        )

    # =====================================================
    # INFORMAÇÕES
    # =====================================================

    print()
    print("=" * 60)
    print("PREPARAÇÃO DO DATASET")
    print("=" * 60)

    print()
    print(
        f"Total de amostras: {len(X)}"
    )

    print(
        f"Formato de X: {X.shape}"
    )

    print(
        f"Formato de y: {y.shape}"
    )

    print()

    print("Classes:")

    for indice, nome in enumerate(
        nomes_classes
    ):

        quantidade = np.sum(
            y == indice
        )

        print(
            f"  [{indice}] "
            f"{nome}: "
            f"{quantidade}"
        )

    # =====================================================
    # DIVISÃO TREINO / TESTE
    # =====================================================

    try:

        X_train, X_test, y_train, y_test = (
            train_test_split(
                X,
                y,
                test_size=0.20,
                random_state=42,
                stratify=y
            )
        )

    except ValueError as erro:

        logger.error(
            "Não foi possível realizar "
            f"a divisão estratificada: {erro}"
        )

        return (
            None,
            None,
            None,
            None,
            nomes_classes
        )

    # =====================================================
    # RESULTADO
    # =====================================================

    print()
    print("-" * 60)
    print("DIVISÃO DO DATASET")
    print("-" * 60)

    print()

    print(
        f"Treinamento: "
        f"{len(X_train)} amostras"
    )

    print(
        f"Teste: "
        f"{len(X_test)} amostras"
    )

    print()

    print(
        f"X_train: "
        f"{X_train.shape}"
    )

    print(
        f"X_test: "
        f"{X_test.shape}"
    )

    print(
        f"y_train: "
        f"{y_train.shape}"
    )

    print(
        f"y_test: "
        f"{y_test.shape}"
    )

    print()

    print("=" * 60)
    print("DATASET PREPARADO COM SUCESSO!")
    print("=" * 60)
    print()

    return (
        X_train,
        X_test,
        y_train,
        y_test,
        nomes_classes
    )


if __name__ == "__main__":

    preparar_dataset()  