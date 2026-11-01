from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    LSTM,
    Dense,
    Dropout,
    Input
)
from tensorflow.keras.regularizers import l2


def criar_modelo(
    frames=60,
    features=126,
    quantidade_classes=3
):
    """
    Cria o modelo LSTM para classificação
    de sequências de sinais em Libras.

    Entrada:
        60 frames
        126 features por frame

    Saída:
        Uma classe entre os sinais disponíveis.
    """

    modelo = Sequential([

        # =================================================
        # ENTRADA
        # =================================================

        Input(
            shape=(
                frames,
                features
            )
        ),

        # =================================================
        # PRIMEIRA LSTM
        # =================================================

        LSTM(
            128,
            return_sequences=True,
            dropout=0.2,
            recurrent_dropout=0.1
        ),

        # =================================================
        # SEGUNDA LSTM
        # =================================================

        LSTM(
            64,
            dropout=0.2,
            recurrent_dropout=0.1
        ),

        # =================================================
        # CAMADA INTERMEDIÁRIA
        # =================================================

        Dense(
            64,
            activation="relu",
            kernel_regularizer=l2(0.001)
        ),

        Dropout(
            0.3
        ),

        # =================================================
        # SAÍDA
        # =================================================

        Dense(
            quantidade_classes,
            activation="softmax"
        )
    ])

    # =====================================================
    # COMPILAÇÃO
    # =====================================================

    modelo.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=[
            "accuracy"
        ]
    )

    return modelo