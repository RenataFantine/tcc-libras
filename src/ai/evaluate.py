import numpy as np

from tensorflow.keras.models import load_model
from sklearn.metrics import (
    confusion_matrix,
    classification_report
)

from src.dataset.prepare import preparar_dataset
from src.utils.logger import setup_logger


logger = setup_logger()


MODEL_PATH = "models/libras_model.keras"


def avaliar_modelo():

    # =====================================================
    # CARREGAR DATASET
    # =====================================================

    (
        X_train,
        X_test,
        y_train,
        y_test,
        nomes_classes
    ) = preparar_dataset()

    if X_test is None:

        logger.error(
            "Não foi possível carregar "
            "o conjunto de teste."
        )

        return

    # =====================================================
    # CARREGAR MODELO
    # =====================================================

    try:

        modelo = load_model(
            MODEL_PATH
        )

    except Exception as erro:

        logger.error(
            f"Erro ao carregar modelo: {erro}"
        )

        return

    print()
    print("=" * 65)
    print("AVALIAÇÃO DETALHADA DO MODELO")
    print("=" * 65)
    print()

    # =====================================================
    # PREVISÕES
    # =====================================================

    probabilidades = modelo.predict(
        X_test,
        verbose=0
    )

    previsoes = np.argmax(
        probabilidades,
        axis=1
    )

    # =====================================================
    # RESULTADO POR AMOSTRA
    # =====================================================

    print(
        "--- RESULTADO DAS AMOSTRAS DE TESTE ---"
    )
    print()

    acertos = 0

    for indice in range(
        len(y_test)
    ):

        classe_real = nomes_classes[
            y_test[indice]
        ]

        classe_prevista = nomes_classes[
            previsoes[indice]
        ]

        confianca = (
            probabilidades[indice][
                previsoes[indice]
            ] * 100
        )

        if (
            y_test[indice]
            == previsoes[indice]
        ):

            resultado = "✅ ACERTO"

            acertos += 1

        else:

            resultado = "❌ ERRO"

        print(
            f"Amostra {indice + 1}: "
            f"Real = {classe_real:<10} | "
            f"Previsto = {classe_prevista:<10} | "
            f"Confiança = {confianca:6.2f}% | "
            f"{resultado}"
        )

    # =====================================================
    # ACURÁCIA
    # =====================================================

    acuracia = (
        acertos / len(y_test)
    ) * 100

    print()
    print(
        f"Amostras corretas: "
        f"{acertos}/{len(y_test)}"
    )

    print(
        f"Acurácia no conjunto de teste: "
        f"{acuracia:.2f}%"
    )

    # =====================================================
    # MATRIZ DE CONFUSÃO
    # =====================================================

    matriz = confusion_matrix(
        y_test,
        previsoes,
        labels=range(
            len(nomes_classes)
        )
    )

    print()
    print(
        "--- MATRIZ DE CONFUSÃO ---"
    )
    print()

    # Cabeçalho
    print(
        f"{'Real / Previsto':<18}",
        end=""
    )

    for nome in nomes_classes:

        print(
            f"{nome:<12}",
            end=""
        )

    print()

    # Linhas
    for indice, nome in enumerate(
        nomes_classes
    ):

        print(
            f"{nome:<18}",
            end=""
        )

        for valor in matriz[indice]:

            print(
                f"{valor:<12}",
                end=""
            )

        print()

    # =====================================================
    # RELATÓRIO
    # =====================================================

    print()
    print(
        "--- RELATÓRIO DE CLASSIFICAÇÃO ---"
    )
    print()

    print(
        classification_report(
            y_test,
            previsoes,
            labels=range(
                len(nomes_classes)
            ),
            target_names=nomes_classes,
            zero_division=0
        )
    )

    print("=" * 65)
    print("AVALIAÇÃO FINALIZADA!")
    print("=" * 65)
    print()


if __name__ == "__main__":

    avaliar_modelo()