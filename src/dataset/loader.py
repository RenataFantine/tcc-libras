
import csv
import os

import numpy as np

from src.utils.logger import setup_logger
from src.dataset.config import (
    DATASET_PATH,
    FRAMES_PER_SEQUENCE
)


logger = setup_logger()


# =========================================================
# CONFIGURAÇÃO DAS CLASSES
# =========================================================

# Ordem fixa para manter compatibilidade entre
# treinamento e previsão.

CLASSES_ESPERADAS = [
    "ajuda",
    "indefinido",
    "obrigado",
    "oi"
]


# =========================================================
# CONFIGURAÇÃO DAS FEATURES
# =========================================================

LANDMARKS = 21

COORDINATES_PER_LANDMARK = 3

FEATURES_PER_HAND = (
    LANDMARKS * COORDINATES_PER_LANDMARK
)

FEATURES_PER_FRAME = (
    FEATURES_PER_HAND * 2
)

# Formato antigo: apenas uma mão.
LEGACY_FEATURES_PER_FRAME = FEATURES_PER_HAND


# =========================================================
# CARREGAR SEQUÊNCIA
# =========================================================

def carregar_sequencia(caminho):
    """
    Carrega uma sequência individual de um CSV.

    Formato atual:
        126 features por frame.

    Formato antigo:
        63 features por frame.

    O formato antigo recebe 63 zeros para
    representar a mão ausente.

    Resultado:
        (frames, 126)
    """

    dados = []

    try:

        with open(
            caminho,
            mode="r",
            newline="",
            encoding="utf-8"
        ) as arquivo:

            reader = csv.reader(arquivo)

            # Ignora o cabeçalho.
            next(reader, None)

            for numero_linha, linha in enumerate(
                reader,
                start=2
            ):

                # Ignora linhas vazias.
                if not linha:
                    continue

                # Remove a coluna frame.
                coordenadas = linha[1:]

                valores = [
                    float(valor)
                    for valor in coordenadas
                ]

                # -----------------------------------------
                # FORMATO ANTIGO: 63 FEATURES
                # -----------------------------------------

                if len(valores) == LEGACY_FEATURES_PER_FRAME:

                    esquerda = (
                        [0.0] * FEATURES_PER_HAND
                    )

                    valores = esquerda + valores

                # -----------------------------------------
                # FORMATO ATUAL: 126 FEATURES
                # -----------------------------------------

                elif len(valores) == FEATURES_PER_FRAME:

                    pass

                # -----------------------------------------
                # FORMATO INVÁLIDO
                # -----------------------------------------

                else:

                    logger.warning(
                        f"{caminho}, linha {numero_linha}: "
                        f"{len(valores)} features encontradas. "
                        f"Esperado: 63 ou 126."
                    )

                    return None

                # -----------------------------------------
                # VERIFICA VALORES
                # -----------------------------------------

                if not np.all(np.isfinite(valores)):

                    logger.warning(
                        f"{caminho}: valores inválidos encontrados."
                    )

                    return None

                dados.append(valores)

    except Exception as erro:

        logger.error(
            f"Erro ao carregar {caminho}: {erro}"
        )

        return None

    if not dados:

        logger.warning(
            f"{caminho}: arquivo sem dados."
        )

        return None

    return np.array(
        dados,
        dtype=np.float32
    )


# =========================================================
# VALIDAR SEQUÊNCIA
# =========================================================

def validar_formato_sequencia(
    sequencia,
    caminho
):
    """
    Verifica se a sequência possui o formato esperado.

    Esperado:
        60 frames
        126 features por frame.
    """

    if sequencia is None:
        return False

    # -----------------------------------------------------
    # DIMENSÕES
    # -----------------------------------------------------

    if sequencia.ndim != 2:

        logger.warning(
            f"{caminho}: formato inválido."
        )

        return False

    frames, features = sequencia.shape

    # -----------------------------------------------------
    # FRAMES
    # -----------------------------------------------------

    if frames != FRAMES_PER_SEQUENCE:

        logger.warning(
            f"{caminho}: {frames} frames encontrados. "
            f"Esperado: {FRAMES_PER_SEQUENCE}."
        )

        return False

    # -----------------------------------------------------
    # FEATURES
    # -----------------------------------------------------

    if features != FEATURES_PER_FRAME:

        logger.warning(
            f"{caminho}: {features} features encontradas. "
            f"Esperado: {FEATURES_PER_FRAME}."
        )

        return False

    # -----------------------------------------------------
    # VALORES NUMÉRICOS
    # -----------------------------------------------------

    if not np.all(np.isfinite(sequencia)):

        logger.warning(
            f"{caminho}: sequência contém valores inválidos."
        )

        return False

    return True


# =========================================================
# CARREGAR DATASET
# =========================================================

def carregar_dataset():
    """
    Carrega todas as classes do dataset.

    Retorna:

        X:
            (amostras, frames, 126)

        y:
            índices das classes.

        nomes_classes:
            nomes dos sinais na ordem definida.
    """

    X = []

    y = []

    nomes_classes = []

    # =====================================================
    # VERIFICA DATASET
    # =====================================================

    if not os.path.exists(DATASET_PATH):

        logger.error(
            f"Dataset não encontrado: {DATASET_PATH}"
        )

        return (
            np.array([]),
            np.array([]),
            []
        )

    # =====================================================
    # DESCOBRE CLASSES DISPONÍVEIS
    # =====================================================

    pastas_disponiveis = [
        pasta
        for pasta in os.listdir(DATASET_PATH)
        if os.path.isdir(
            os.path.join(DATASET_PATH, pasta)
        )
    ]

    # Mantém somente as classes esperadas,
    # respeitando a ordem fixa.

    pastas = [
        classe
        for classe in CLASSES_ESPERADAS
        if classe in pastas_disponiveis
    ]

    # Verifica classes ausentes.

    classes_ausentes = [
        classe
        for classe in CLASSES_ESPERADAS
        if classe not in pastas_disponiveis
    ]

    if classes_ausentes:

        logger.warning(
            f"Classes ausentes: {classes_ausentes}"
        )

    # Verifica pastas extras.

    classes_extras = [
        classe
        for classe in pastas_disponiveis
        if classe not in CLASSES_ESPERADAS
    ]

    if classes_extras:

        logger.warning(
            f"Pastas ignoradas: {classes_extras}"
        )

    if not pastas:

        logger.error(
            "Nenhuma classe válida encontrada."
        )

        return (
            np.array([]),
            np.array([]),
            []
        )

    nomes_classes = pastas

    mapa_classes = {
        nome: indice
        for indice, nome in enumerate(nomes_classes)
    }

    # =====================================================
    # CARREGA CADA CLASSE
    # =====================================================

    for nome_classe in nomes_classes:

        pasta_classe = os.path.join(
            DATASET_PATH,
            nome_classe
        )

        arquivos = sorted(
            arquivo
            for arquivo in os.listdir(pasta_classe)
            if arquivo.lower().endswith(".csv")
        )

        quantidade_valida = 0

        quantidade_invalida = 0

        logger.info(
            f"Carregando classe: {nome_classe}"
        )

        # ---------------------------------------------
        # CARREGA ARQUIVOS
        # ---------------------------------------------

        for arquivo in arquivos:

            caminho = os.path.join(
                pasta_classe,
                arquivo
            )

            sequencia = carregar_sequencia(
                caminho
            )

            # -----------------------------------------
            # VALIDA
            # -----------------------------------------

            if not validar_formato_sequencia(
                sequencia,
                caminho
            ):

                quantidade_invalida += 1

                logger.warning(
                    f"Sequência ignorada: {caminho}"
                )

                continue

            # -----------------------------------------
            # ADICIONA
            # -----------------------------------------

            X.append(sequencia)

            y.append(
                mapa_classes[nome_classe]
            )

            quantidade_valida += 1

        logger.info(
            f"Classe '{nome_classe}': "
            f"{quantidade_valida} válidas, "
            f"{quantidade_invalida} inválidas."
        )

    # =====================================================
    # CONVERTE PARA NUMPY
    # =====================================================

    if not X:

        logger.error(
            "Nenhuma sequência válida foi carregada."
        )

        return (
            np.array([]),
            np.array([]),
            nomes_classes
        )

    X = np.array(
        X,
        dtype=np.float32
    )

    y = np.array(
        y,
        dtype=np.int32
    )

    return (
        X,
        y,
        nomes_classes
    )


# =========================================================
# RESUMO
# =========================================================

def mostrar_resumo(
    X,
    y,
    nomes_classes
):
    """
    Exibe um resumo do dataset carregado.
    """

    print()

    print("=" * 60)

    print("RESUMO DO DATASET")

    print("=" * 60)

    print()

    print(
        f"Total de amostras: {len(X)}"
    )

    print(
        f"Frames por amostra: {FRAMES_PER_SEQUENCE}"
    )

    print(
        f"Features por mão: {FEATURES_PER_HAND}"
    )

    print(
        f"Features por frame: {FEATURES_PER_FRAME}"
    )

    print()

    print(
        f"Formato de X: {X.shape}"
    )

    print(
        f"Formato de y: {y.shape}"
    )

    print()

    print("Classes:")

    for indice, nome in enumerate(nomes_classes):

        quantidade = np.sum(
            y == indice
        )

        print(
            f"  [{indice}] {nome}: "
            f"{quantidade} amostras"
        )

    print()

    print("=" * 60)

    print()


# =========================================================
# EXECUÇÃO
# =========================================================

if __name__ == "__main__":

    X, y, nomes_classes = carregar_dataset()

    if len(X) > 0:

        mostrar_resumo(
            X,
            y,
            nomes_classes
        )

    else:

        print(
            "Nenhuma sequência válida foi carregada."
        )
