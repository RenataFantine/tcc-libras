
import cv2
import json
import os
import numpy as np
import mediapipe as mp

from collections import deque
from PIL import Image, ImageDraw, ImageFont
from tensorflow.keras.models import load_model

from src.vision.hands import HandDetector
from src.vision.landmarks import extract_normalized_hands
from src.audio.audio import falar_sinal
from src.translation.translator import (
    traduzir_sinal,
    adicionar_sinal
)


# =========================
# CONFIGURAÇÕES
# =========================

MODEL_PATH = "models/libras_model_teste.keras"
CLASSES_PATH = "models/libras_model_teste_classes.json"

FRAMES_PER_SEQUENCE = 60
MAX_NUM_HANDS = 2

MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.7

CONFIDENCE_THRESHOLD = 0.70
STABLE_PREDICTIONS = 5
COOLDOWN_FRAMES = 30

NOMES_CLASSES = []


def carregar_nomes_classes():
    """Carrega a ordem das classes salva durante o treinamento."""

    if not os.path.exists(CLASSES_PATH):
        raise FileNotFoundError(
            f"Arquivo de classes não encontrado: {CLASSES_PATH}"
        )

    with open(CLASSES_PATH, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    nomes = dados.get("classes", [])

    if not nomes:
        raise ValueError("O arquivo de classes está vazio ou inválido.")

    return nomes


# =========================
# CORES DA INTERFACE
# =========================

AZUL_PAINEL = (100, 70, 40)
AZUL_BARRA = (255, 220, 180)

BRANCO = (240, 248, 255)
AZUL_CLARO = (210, 230, 245)
AZUL_TEXTO = (175, 205, 230)


# =========================
# FONTES
# =========================

def carregar_fontes():
    """Carrega fontes Unicode disponíveis no Windows."""

    caminhos = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibri.ttf"
    ]

    for caminho in caminhos:

        try:

            fonte_normal = ImageFont.truetype(caminho, 18)
            fonte_pequena = ImageFont.truetype(caminho, 15)
            fonte_titulo = ImageFont.truetype(caminho, 19)
            fonte_destaque = ImageFont.truetype(caminho, 22)

            return (
                fonte_normal,
                fonte_pequena,
                fonte_titulo,
                fonte_destaque
            )

        except OSError:
            continue

    fonte = ImageFont.load_default()

    return (
        fonte,
        fonte,
        fonte,
        fonte
    )


# =========================
# PAINEL
# =========================

def desenhar_painel(frame, x, y, largura, altura):
    """Desenha um painel azul semitransparente."""

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (x, y),
        (x + largura, y + altura),
        AZUL_PAINEL,
        -1
    )

    cv2.addWeighted(
        overlay,
        0.70,
        frame,
        0.30,
        0,
        frame
    )


# =========================
# INTERFACE
# =========================

def desenhar_interface(
    frame,
    classe,
    traducao,
    confianca,
    status,
    quantidade_frames,
    fontes
):
    """Desenha os elementos visuais da interface."""

    (
        fonte_normal,
        fonte_pequena,
        fonte_titulo,
        fonte_destaque
    ) = fontes

    altura, largura = frame.shape[:2]

    # Barra de progresso
    largura_barra = 230
    altura_barra = 10

    x_barra = 25
    y_barra = 128

    progresso = min(
        quantidade_frames / FRAMES_PER_SEQUENCE,
        1.0
    )

    preenchimento = int(
        largura_barra * progresso
    )

    cv2.rectangle(
        frame,
        (x_barra, y_barra),
        (
            x_barra + largura_barra,
            y_barra + altura_barra
        ),
        (100, 120, 145),
        1
    )

    cv2.rectangle(
        frame,
        (x_barra, y_barra),
        (
            x_barra + preenchimento,
            y_barra + altura_barra
        ),
        AZUL_BARRA,
        -1
    )

    # Painel de status
    painel_largura = 300
    painel_altura = 175

    x_painel = largura - painel_largura - 20
    y_painel = 25

    desenhar_painel(
        frame,
        x_painel,
        y_painel,
        painel_largura,
        painel_altura
    )

    # Painel de tradução
    painel_traducao_altura = 85

    x_traducao = 20

    y_traducao = (
        altura
        - painel_traducao_altura
        - 20
    )

    desenhar_painel(
        frame,
        x_traducao,
        y_traducao,
        largura - 40,
        painel_traducao_altura
    )

    # Pillow
    imagem = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    imagem_pil = Image.fromarray(imagem)
    desenho = ImageDraw.Draw(imagem_pil)

    # Cabeçalho
    desenho.text(
        (25, 22),
        "INTELIGENTE — LIBRAS",
        font=fonte_titulo,
        fill=BRANCO
    )

    desenho.text(
        (25, 52),
        "Posicione suas mãos dentro da área da câmera",
        font=fonte_pequena,
        fill=AZUL_CLARO
    )

    desenho.text(
        (25, 148),
        f"Capturando: {quantidade_frames}/{FRAMES_PER_SEQUENCE}",
        font=fonte_pequena,
        fill=AZUL_CLARO
    )

    # Painel de status
    desenho.text(
        (x_painel + 18, y_painel + 15),
        "SINAL",
        font=fonte_pequena,
        fill=AZUL_TEXTO
    )

    desenho.text(
        (x_painel + 18, y_painel + 38),
        classe,
        font=fonte_destaque,
        fill=BRANCO
    )

    desenho.text(
        (x_painel + 18, y_painel + 75),
        "CONFIANÇA",
        font=fonte_pequena,
        fill=AZUL_TEXTO
    )

    desenho.text(
        (x_painel + 18, y_painel + 98),
        f"{confianca * 100:.1f}%",
        font=fonte_normal,
        fill=BRANCO
    )

    desenho.text(
        (x_painel + 155, y_painel + 75),
        "STATUS",
        font=fonte_pequena,
        fill=AZUL_TEXTO
    )

    desenho.text(
        (x_painel + 155, y_painel + 98),
        status,
        font=fonte_normal,
        fill=BRANCO
    )

    # Tradução
    desenho.text(
        (x_traducao + 18, y_traducao + 10),
        "TRADUÇÃO",
        font=fonte_pequena,
        fill=AZUL_TEXTO
    )

    texto_traducao = traducao

    if len(texto_traducao) > 70:
        texto_traducao = texto_traducao[:67] + "..."

    desenho.text(
        (x_traducao + 18, y_traducao + 35),
        texto_traducao,
        font=fonte_normal,
        fill=BRANCO
    )

    # Volta para OpenCV
    frame[:] = cv2.cvtColor(
        np.array(imagem_pil),
        cv2.COLOR_RGB2BGR
    )


# =========================
# PREVISÃO
# =========================

def prever_sinal(modelo, sequencia):
    """Realiza a previsão utilizando a sequência de landmarks."""

    global NOMES_CLASSES

    # Carrega as classes automaticamente.
    # Isso permite utilizar a função pelo Flask.
    if not NOMES_CLASSES:
        NOMES_CLASSES = carregar_nomes_classes()

    entrada = np.array(
        sequencia,
        dtype=np.float32
    )

    entrada = np.expand_dims(
        entrada,
        axis=0
    )

    previsao = modelo.predict(
        entrada,
        verbose=0
    )[0]

    if len(previsao) != len(NOMES_CLASSES):
        raise ValueError(
            "A saída do modelo não corresponde às classes carregadas. "
            f"Saídas do modelo: {len(previsao)}; "
            f"classes carregadas: {len(NOMES_CLASSES)}."
        )

    indice_classe = np.argmax(previsao)

    confianca = float(
        previsao[indice_classe]
    )

    classe = NOMES_CLASSES[indice_classe]

    print(
        " | ".join(
            [
                f"{nome}: {valor * 100:.2f}%"
                for nome, valor in zip(
                    NOMES_CLASSES,
                    previsao
                )
            ]
        )
    )

    return classe, confianca


# =========================
# RECONHECIMENTO
# =========================

def iniciar_reconhecimento():

    print()
    print("=" * 55)
    print("RECONHECIMENTO DE LIBRAS")
    print("=" * 55)
    print()

    print("Carregando modelo de teste...")

    global NOMES_CLASSES

    NOMES_CLASSES = carregar_nomes_classes()

    modelo = load_model(
        MODEL_PATH
    )

    quantidade_saidas = int(
        modelo.output_shape[-1]
    )

    if quantidade_saidas != len(NOMES_CLASSES):
        raise ValueError(
            "A quantidade de saídas do modelo não corresponde "
            "à quantidade de classes do arquivo JSON. "
            f"Modelo: {quantidade_saidas}; "
            f"classes: {len(NOMES_CLASSES)}."
        )

    print("Modelo carregado com sucesso.")
    print("Classes:")

    for indice, nome in enumerate(NOMES_CLASSES):
        print(f"  [{indice}] {nome}")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Não foi possível abrir a câmera.")
        return

    detector = HandDetector(
        max_num_hands=MAX_NUM_HANDS,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE
    )

    fontes = carregar_fontes()

    sequencia = deque(
        maxlen=FRAMES_PER_SEQUENCE
    )

    ultima_classe = None
    contador_estabilidade = 0

    classe_exibida = "Aguardando..."
    confianca_exibida = 0.0

    traducao_exibida = "Aguardando sinal..."

    mensagem = ""

    sinal_reconhecido = False
    cooldown = 0

    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands

    print("Câmera iniciada.")
    print("Pressione ESC para sair.")
    print()

    while True:

        sucesso, frame = cap.read()

        if not sucesso:
            print("Erro ao capturar frame.")
            break

        frame = cv2.flip(frame, 1)

        resultado = detector.detect(frame)

        # Detecção das mãos
        if resultado.multi_hand_landmarks:

            for hand_landmarks in resultado.multi_hand_landmarks:

                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

            pontos = extract_normalized_hands(resultado)

            if len(pontos) == 126:
                sequencia.append(pontos)

        else:
            # Evita misturar frames antigos com uma nova sequência
            sequencia.clear()
            ultima_classe = None
            contador_estabilidade = 0

        # Cooldown
        if cooldown > 0:
            cooldown -= 1

        # Reconhecimento
        if (
            len(sequencia) == FRAMES_PER_SEQUENCE
            and cooldown == 0
        ):

            classe, confianca = prever_sinal(
                modelo,
                sequencia
            )

            if confianca >= CONFIDENCE_THRESHOLD:

                if classe == ultima_classe:
                    contador_estabilidade += 1
                else:
                    ultima_classe = classe
                    contador_estabilidade = 1

                classe_exibida = classe
                confianca_exibida = confianca

                if (
                    contador_estabilidade >= STABLE_PREDICTIONS
                    and not sinal_reconhecido
                ):

                    sinal_reconhecido = True
                    cooldown = COOLDOWN_FRAMES

                    print()

                    if classe == "indefinido":

                        classe_exibida = "Indefinido"
                        traducao_exibida = "Sinal não reconhecido."

                        print(
                            "Movimento não reconhecido: indefinido"
                        )

                    else:

                        traducao = traduzir_sinal(classe)

                        mensagem = adicionar_sinal(
                            mensagem,
                            classe
                        )

                        traducao_exibida = mensagem

                        print(f"Sinal reconhecido: {classe}")
                        print(f"Tradução: {traducao_exibida}")

                        falar_sinal(classe)

                    print()

                    sequencia.clear()
                    ultima_classe = None
                    contador_estabilidade = 0

            else:

                classe_exibida = "Sinal incerto"
                confianca_exibida = confianca

        # Libera novo sinal após a pausa
        if cooldown == 0 and not resultado.multi_hand_landmarks:
            sinal_reconhecido = False

        # Status
        if cooldown > 0:
            status = "Áudio / pausa"

        elif len(sequencia) < FRAMES_PER_SEQUENCE:
            status = "Capturando"

        elif contador_estabilidade > 0:
            status = "Confirmando"

        else:
            status = "Analisando"

        # Interface
        desenhar_interface(
            frame,
            classe_exibida,
            traducao_exibida,
            confianca_exibida,
            status,
            len(sequencia),
            fontes
        )

        cv2.imshow(
            "Totem Inteligente - Libras",
            frame
        )

        # Saída
        tecla = cv2.waitKey(1) & 0xFF

        if tecla == 27:
            break

    detector.close()
    cap.release()
    cv2.destroyAllWindows()

    print()
    print("Reconhecimento encerrado.")
    print()


if __name__ == "__main__":
    iniciar_reconhecimento()
