
import csv
import os
import time

import cv2
import mediapipe as mp

from src.utils.logger import setup_logger
from src.vision.hands import HandDetector
from src.vision.landmarks import extract_normalized_hands

from src.dataset.config import (
    MAX_NUM_HANDS,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    FRAMES_PER_SEQUENCE,
    START_KEY,
    EXIT_KEY,
    DATASET_PATH,
    SIGNAL_NAME,
    MAX_MISSED_FRAMES
)


logger = setup_logger()

mp_drawing = mp.solutions.drawing_utils


# =========================================================
# CONFIGURAÇÃO DA PREPARAÇÃO
# =========================================================

TEMPO_PREPARACAO = 3


# =========================================================
# CONFIGURAÇÃO DOS SINAIS
# =========================================================

# Sinais que utilizam apenas uma mão.
SINAIS_UMA_MAO = [
    "oi"
]

# Sinais que aceitam uma ou duas mãos.
SINAIS_MAOS_VARIAVEIS = [
    "indefinido"
]


def sinal_precisa_duas_maos():
    """
    Verifica se o sinal atual exige obrigatoriamente
    duas mãos.

    Retorna:
        True  -> duas mãos obrigatórias
        False -> uma ou duas mãos permitidas
    """

    nome = SIGNAL_NAME.lower()

    return (
        nome not in SINAIS_UMA_MAO
        and nome not in SINAIS_MAOS_VARIAVEIS
    )


def sinal_precisa_maos_variaveis():
    """
    Verifica se o sinal aceita uma ou duas mãos.
    """

    return SIGNAL_NAME.lower() in SINAIS_MAOS_VARIAVEIS


def obter_texto_maos():
    """
    Retorna a descrição da quantidade de mãos
    necessária para o sinal atual.
    """

    if sinal_precisa_maos_variaveis():
        return "1 ou 2 mãos"

    if sinal_precisa_duas_maos():
        return "2 mãos"

    return "1 mão"


def obter_instrucao_maos():
    """
    Retorna a instrução exibida na câmera.
    """

    if sinal_precisa_maos_variaveis():
        return "COLOQUE UMA OU DUAS MAOS NA CAMERA"

    if sinal_precisa_duas_maos():
        return "COLOQUE AS DUAS MAOS NA CAMERA"

    return "COLOQUE UMA MAO NA CAMERA"


# =========================================================
# DATASET
# =========================================================

def criar_pasta_dataset():
    """
    Cria a pasta do sinal caso ela ainda não exista.
    """

    pasta = os.path.join(
        DATASET_PATH,
        SIGNAL_NAME
    )

    os.makedirs(
        pasta,
        exist_ok=True
    )

    return pasta


def proximo_numero_amostra(pasta):
    """
    Descobre o próximo número disponível para a amostra.
    Evita sobrescrever arquivos existentes.
    """

    numeros = []

    for arquivo in os.listdir(pasta):

        if not arquivo.endswith(".csv"):
            continue

        nome = os.path.splitext(arquivo)[0]

        try:
            numeros.append(int(nome))

        except ValueError:
            continue

    if not numeros:
        return 1

    return max(numeros) + 1


def criar_cabecalho():
    """
    Cria o cabeçalho do CSV.

    Cada frame possui:
        63 features da mão esquerda
        63 features da mão direita

    Total: 126 features.
    """

    cabecalho = ["frame"]

    for lado in ["left", "right"]:

        for ponto in range(21):

            cabecalho.extend([
                f"{lado}_p{ponto}_x",
                f"{lado}_p{ponto}_y",
                f"{lado}_p{ponto}_z"
            ])

    return cabecalho


def salvar_sequencia(
    sequencia,
    numero_amostra,
    pasta
):
    """
    Salva uma sequência completa em CSV.

    Cada linha representa um frame.
    """

    caminho = os.path.join(
        pasta,
        f"{numero_amostra:03d}.csv"
    )

    try:

        with open(
            caminho,
            mode="w",
            newline="",
            encoding="utf-8"
        ) as arquivo:

            writer = csv.writer(arquivo)

            # Cabeçalho
            writer.writerow(
                criar_cabecalho()
            )

            # Dados dos frames
            for numero_frame, pontos in enumerate(
                sequencia,
                start=1
            ):

                writer.writerow(
                    [numero_frame] + pontos
                )

        logger.info(
            f"Sequência salva: {caminho}"
        )

        print()
        print(
            f"✅ Sequência salva em: {caminho}"
        )

    except Exception as erro:

        logger.error(
            f"Erro ao salvar sequência: {erro}"
        )

        print(
            f"❌ Erro ao salvar sequência: {erro}"
        )


# =========================================================
# COLETOR
# =========================================================

def iniciar_coleta():

    # =====================================================
    # PREPARAÇÃO DO DATASET
    # =====================================================

    pasta_dataset = criar_pasta_dataset()

    numero_amostra = proximo_numero_amostra(
        pasta_dataset
    )

    duas_maos_necessarias = sinal_precisa_duas_maos()

    # =====================================================
    # INFORMAÇÕES DO SINAL
    # =====================================================

    print()
    print("=" * 60)
    print("CONFIGURAÇÃO DA COLETA")
    print("=" * 60)

    print(
        f"Sinal: {SIGNAL_NAME}"
    )

    print(
        f"Mãos necessárias: {obter_texto_maos()}"
    )

    print(
        f"Próxima amostra: {numero_amostra}"
    )

    print(
        f"Frames por sequência: {FRAMES_PER_SEQUENCE}"
    )

    print("=" * 60)
    print()

    # =====================================================
    # CÂMERA
    # =====================================================

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():

        logger.error(
            "Não foi possível abrir a câmera."
        )

        print(
            "❌ Não foi possível abrir a câmera."
        )

        return

    # =====================================================
    # DETECTOR
    # =====================================================

    detector = HandDetector(
        max_num_hands=MAX_NUM_HANDS,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE
    )

    logger.info(
        "Coletor iniciado."
    )

    # =====================================================
    # ESTADOS DA COLETA
    # =====================================================

    gravando = False

    preparando = False

    sequencia = []

    frames_perdidos = 0

    tempo_inicio_preparacao = 0

    ultimo_numero_contagem = None

    # =====================================================
    # LOOP PRINCIPAL
    # =====================================================

    try:

        while True:

            # -------------------------------------------------
            # CAPTURA FRAME
            # -------------------------------------------------

            ret, frame = cap.read()

            if not ret:

                logger.error(
                    "Erro ao capturar frame."
                )

                print(
                    "❌ Erro ao capturar frame."
                )

                break

            # -------------------------------------------------
            # ESPELHAMENTO
            # -------------------------------------------------

            frame = cv2.flip(
                frame,
                1
            )

            # -------------------------------------------------
            # DETECÇÃO DAS MÃOS
            # -------------------------------------------------

            resultado = detector.detect(
                frame
            )

            # =================================================
            # QUANTIDADE DE MÃOS
            # =================================================

            quantidade_maos = 0

            if (
                resultado
                and resultado.multi_hand_landmarks
            ):

                quantidade_maos = len(
                    resultado.multi_hand_landmarks
                )

            # =================================================
            # VERIFICA QUANTIDADE SUFICIENTE
            # =================================================

            if duas_maos_necessarias:

                maos_suficientes = (
                    quantidade_maos >= 2
                )

            else:

                # Para "oi" e "indefinido",
                # uma ou duas mãos são aceitas.
                maos_suficientes = (
                    quantidade_maos >= 1
                )

            # =================================================
            # DESENHA AS MÃOS
            # =================================================

            if (
                resultado
                and resultado.multi_hand_landmarks
            ):

                for hand_landmarks in (
                    resultado.multi_hand_landmarks
                ):

                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp.solutions.hands.HAND_CONNECTIONS
                    )

            # =================================================
            # PREPARAÇÃO
            # =================================================

            if preparando:

                # ---------------------------------------------
                # VERIFICA MÃOS
                # ---------------------------------------------

                if not maos_suficientes:

                    texto = obter_instrucao_maos()

                    cv2.putText(
                        frame,
                        texto,
                        (20, 45),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.75,
                        (0, 255, 255),
                        2
                    )

                else:

                    # -----------------------------------------
                    # CALCULA TEMPO
                    # -----------------------------------------

                    tempo_decorrido = (
                        time.time()
                        - tempo_inicio_preparacao
                    )

                    restante = (
                        TEMPO_PREPARACAO
                        - int(tempo_decorrido)
                    )

                    # -----------------------------------------
                    # CONTAGEM
                    # -----------------------------------------

                    if restante > 0:

                        texto = (
                            f"PREPARE-SE: {restante}"
                        )

                        if (
                            ultimo_numero_contagem
                            != restante
                        ):

                            print(
                                f"⏳ {restante}..."
                            )

                            ultimo_numero_contagem = (
                                restante
                            )

                    else:

                        # -------------------------------------
                        # COMEÇA A GRAVAÇÃO
                        # -------------------------------------

                        preparando = False

                        gravando = True

                        sequencia = []

                        frames_perdidos = 0

                        ultimo_numero_contagem = None

                        print()
                        print(
                            f"🎥 GRAVANDO AMOSTRA {numero_amostra}!"
                        )

                        print(
                            f"Quantidade de mãos: {quantidade_maos}"
                        )

                        print(
                            "Faça o sinal agora!"
                        )

                        texto = "COMECE!"

            # =================================================
            # GRAVAÇÃO
            # =================================================

            elif gravando:

                # -------------------------------------------------
                # MÃOS DETECTADAS
                # -------------------------------------------------

                if (
                    resultado
                    and resultado.multi_hand_landmarks
                ):

                    # ---------------------------------------------
                    # VERIFICA QUANTIDADE DE MÃOS
                    # ---------------------------------------------

                    if maos_suficientes:

                        frames_perdidos = 0

                        # -----------------------------------------
                        # EXTRAI OS LANDMARKS
                        # -----------------------------------------

                        pontos_normalizados = (
                            extract_normalized_hands(
                                resultado
                            )
                        )

                        # -----------------------------------------
                        # VALIDA 126 FEATURES
                        # -----------------------------------------

                        if len(
                            pontos_normalizados
                        ) != 126:

                            logger.error(
                                "Quantidade inválida de features: "
                                f"{len(pontos_normalizados)}"
                            )

                            print(
                                "❌ Erro: esperado 126 features."
                            )

                        else:

                            # -------------------------------------
                            # ADICIONA FRAME
                            # -------------------------------------

                            sequencia.append(
                                pontos_normalizados
                            )

                            quantidade = len(
                                sequencia
                            )

                            print(
                                f"Frame: {quantidade}/"
                                f"{FRAMES_PER_SEQUENCE}"
                            )

                            # -------------------------------------
                            # SEQUÊNCIA COMPLETA
                            # -------------------------------------

                            if (
                                quantidade
                                >= FRAMES_PER_SEQUENCE
                            ):

                                salvar_sequencia(
                                    sequencia,
                                    numero_amostra,
                                    pasta_dataset
                                )

                                numero_amostra += 1

                                sequencia = []

                                gravando = False

                                frames_perdidos = 0

                                print()
                                print(
                                    "✅ Pronto!"
                                )

                                print(
                                    "Você pode coletar outra sequência."
                                )

                    else:

                        frames_perdidos += 1

                        print(
                            f"Quantidade incorreta de mãos: "
                            f"{quantidade_maos}"
                        )

                        print(
                            f"Frames inválidos: {frames_perdidos}/"
                            f"{MAX_MISSED_FRAMES}"
                        )

                        if (
                            frames_perdidos
                            >= MAX_MISSED_FRAMES
                        ):

                            print()
                            print(
                                "⚠️ Quantidade de mãos incorreta "
                                "por muito tempo."
                            )

                            print(
                                "❌ Sequência cancelada."
                            )

                            gravando = False

                            sequencia = []

                            frames_perdidos = 0

                # -------------------------------------------------
                # NENHUMA MÃO DETECTADA
                # -------------------------------------------------

                else:

                    frames_perdidos += 1

                    print(
                        f"Mãos não detectadas: {frames_perdidos}/"
                        f"{MAX_MISSED_FRAMES}"
                    )

                    # ---------------------------------------------
                    # CANCELAMENTO
                    # ---------------------------------------------

                    if (
                        frames_perdidos
                        >= MAX_MISSED_FRAMES
                    ):

                        print()
                        print(
                            "⚠️ Mãos perdidas por muito tempo."
                        )

                        print(
                            "❌ Sequência cancelada."
                        )

                        gravando = False

                        sequencia = []

                        frames_perdidos = 0

            # =================================================
            # TEXTO NORMAL DA TELA
            # =================================================

            else:

                texto = (
                    f"Pressione S para iniciar uma coleta "
                    f"({obter_texto_maos()})"
                )

            # =================================================
            # TEXTO DE GRAVAÇÃO
            # =================================================

            if gravando:

                texto = (
                    f"GRAVANDO: {len(sequencia)}/"
                    f"{FRAMES_PER_SEQUENCE}"
                )

            # =================================================
            # TEXTO DE PREPARAÇÃO
            # =================================================

            elif preparando:

                if maos_suficientes:

                    tempo_decorrido = (
                        time.time()
                        - tempo_inicio_preparacao
                    )

                    restante = max(
                        0,
                        TEMPO_PREPARACAO
                        - int(tempo_decorrido)
                    )

                    if restante > 0:

                        texto = (
                            f"PREPARE-SE: {restante}"
                        )

                    else:

                        texto = "COMECE!"

                else:

                    texto = obter_instrucao_maos()

            # =================================================
            # TEXTO NA TELA
            # =================================================

            cv2.putText(
                frame,
                texto,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 255, 0),
                2
            )

            # =================================================
            # EXIBE CÂMERA
            # =================================================

            cv2.imshow(
                "Coleta de Dataset - TCC Libras",
                frame
            )

            # =================================================
            # TECLADO
            # =================================================

            tecla = cv2.waitKey(1) & 0xFF

            # =================================================
            # INICIAR COLETA
            # =================================================

            if (
                tecla == START_KEY
                and not gravando
                and not preparando
            ):

                sequencia = []

                frames_perdidos = 0

                preparando = True

                tempo_inicio_preparacao = (
                    time.time()
                )

                ultimo_numero_contagem = None

                print()
                print("=" * 60)

                print(
                    f"Preparando amostra {numero_amostra}..."
                )

                print(
                    f"Posicione as mãos: {obter_texto_maos()}."
                )

                print(
                    "A gravação começará automaticamente."
                )

                print("=" * 60)

            # =================================================
            # ENCERRAR
            # =================================================

            if tecla == EXIT_KEY:

                break

    except Exception as erro:

        logger.exception(
            f"Erro durante a coleta: {erro}"
        )

        print(
            f"❌ Erro durante a coleta: {erro}"
        )

    finally:

        # =====================================================
        # ENCERRAMENTO
        # =====================================================

        detector.close()

        cap.release()

        cv2.destroyAllWindows()

        logger.info(
            "Coletor encerrado."
        )

        print()
        print(
            "Coletor encerrado."
        )


# =========================================================
# EXECUÇÃO
# =========================================================

if __name__ == "__main__":

    iniciar_coleta()
