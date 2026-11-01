
import threading
from collections import deque
from pathlib import Path

import cv2
import mediapipe as mp

from tensorflow.keras.models import load_model

from src.ai.predict import (
    FRAMES_PER_SEQUENCE,
    MAX_NUM_HANDS,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    CONFIDENCE_THRESHOLD,
    STABLE_PREDICTIONS,
    prever_sinal,
)

from src.vision.hands import HandDetector
from src.vision.landmarks import extract_normalized_hands
from src.translation.translator import adicionar_sinal
from src.audio.audio import falar_sinal

from src.database.repository import (
    buscar_sinal,
    registrar_reconhecimento,
)


# ==================================================
# CAMINHO DO MODELO
# ==================================================

RAIZ_PROJETO = Path(__file__).resolve().parents[2]

# Utiliza o modelo experimental atualizado.
# O modelo original permanece preservado.
MODEL_PATH = RAIZ_PROJETO / "models" / "libras_model_teste.keras"


# ==================================================
# SERVIÇO DE RECONHECIMENTO
# ==================================================

class RecognitionService:

    def __init__(self):

        self._lock = threading.Lock()
        self._thread = None
        self._stop_event = threading.Event()
        self._camera = None

        self._latest_frame = None

        self._state = {
            "running": False,
            "sinal": None,
            "traducao": "Aguardando sinal...",
            "confianca": 0.0,
            "status": "Parado",
            "erro": None,
            "frames": 0,
            "total_frames": FRAMES_PER_SEQUENCE,
            "maos_detectadas": False,
        }

    # ==================================================
    # CONSULTAR ESTADO
    # ==================================================

    def get_state(self):

        with self._lock:
            return self._state.copy()

    # ==================================================
    # ATUALIZAR ESTADO
    # ==================================================

    def _update_state(self, **values):

        with self._lock:
            self._state.update(values)

    # ==================================================
    # REGISTRAR RECONHECIMENTO NO BANCO
    # ==================================================

    def _registrar_no_banco(self, classe, confianca):
        """
        Registra somente sinais válidos e cadastrados
        na tabela sinais.
        """

        try:

            # Não registra a classe indefinida.
            if classe == "indefinido":
                return False

            sinal = buscar_sinal(classe)

            if sinal is None:

                print(
                    f"Sinal '{classe}' não encontrado no banco."
                )

                return False

            sinal_id = sinal[0]

            sucesso = registrar_reconhecimento(
                sinal_id,
                confianca,
            )

            if sucesso:

                print(
                    f"Reconhecimento registrado: {classe} "
                    f"({confianca * 100:.2f}%)."
                )

            else:

                print(
                    f"Não foi possível registrar: {classe}."
                )

            return sucesso

        except Exception as erro:

            print(
                f"Erro ao registrar reconhecimento no banco: {erro}"
            )

            return False

    # ==================================================
    # OBTER IMAGEM DA CÂMERA
    # ==================================================

    def get_frame(self):

        with self._lock:

            if self._latest_frame is None:
                return None

            return self._latest_frame

    # ==================================================
    # INICIAR RECONHECIMENTO
    # ==================================================

    def start(self):

        with self._lock:

            if self._state["running"]:
                return False

            self._stop_event.clear()
            self._latest_frame = None

            self._state.update({
                "running": True,
                "sinal": None,
                "traducao": "Aguardando sinal...",
                "confianca": 0.0,
                "status": "Iniciando câmera...",
                "erro": None,
                "frames": 0,
                "total_frames": FRAMES_PER_SEQUENCE,
                "maos_detectadas": False,
            })

            self._thread = threading.Thread(
                target=self._run,
                daemon=True,
            )

            self._thread.start()

        return True

    # ==================================================
    # PARAR RECONHECIMENTO
    # ==================================================

    def stop(self):

        self._stop_event.set()

        self._update_state(
            status="Encerrando reconhecimento..."
        )

    # ==================================================
    # PROCESSAMENTO PRINCIPAL
    # ==================================================

    def _run(self):

        camera = None
        detector = None

        try:

            # ------------------------------------------
            # CARREGAR MODELO ATUALIZADO
            # ------------------------------------------

            if not MODEL_PATH.is_file():

                raise FileNotFoundError(
                    f"Modelo não encontrado: {MODEL_PATH}"
                )

            self._update_state(
                status="Carregando modelo..."
            )

            modelo = load_model(str(MODEL_PATH))

            if self._stop_event.is_set():
                return

            # ------------------------------------------
            # INICIAR CÂMERA
            # ------------------------------------------

            camera = cv2.VideoCapture(0)
            self._camera = camera

            if not camera.isOpened():

                raise RuntimeError(
                    "Não foi possível abrir a câmera."
                )

            detector = HandDetector(
                max_num_hands=MAX_NUM_HANDS,
                min_detection_confidence=MIN_DETECTION_CONFIDENCE,
                min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
            )

            mp_drawing = mp.solutions.drawing_utils
            mp_hands = mp.solutions.hands

            # ------------------------------------------
            # VARIÁVEIS DO RECONHECIMENTO
            # ------------------------------------------

            sequencia = deque(
                maxlen=FRAMES_PER_SEQUENCE
            )

            ultima_classe = None
            contador_estabilidade = 0

            mensagem = ""

            self._update_state(
                status="Aguardando detecção das mãos..."
            )

            # ------------------------------------------
            # LOOP DA CÂMERA
            # ------------------------------------------

            while not self._stop_event.is_set():

                sucesso, frame = camera.read()

                if not sucesso:

                    raise RuntimeError(
                        "Erro ao capturar imagem da câmera."
                    )

                frame = cv2.flip(frame, 1)

                resultado = detector.detect(frame)

                maos_detectadas = bool(
                    resultado
                    and resultado.multi_hand_landmarks
                )

                # --------------------------------------
                # MÃOS DETECTADAS
                # --------------------------------------

                if maos_detectadas:

                    for landmarks in resultado.multi_hand_landmarks:

                        mp_drawing.draw_landmarks(
                            frame,
                            landmarks,
                            mp_hands.HAND_CONNECTIONS,
                        )

                    pontos = extract_normalized_hands(
                        resultado
                    )

                    if len(pontos) == 126:
                        sequencia.append(pontos)

                    self._update_state(
                        maos_detectadas=True,
                        status=(
                            "Mãos detectadas! "
                            "Pode realizar o sinal."
                        ),
                    )

                # --------------------------------------
                # MÃOS NÃO DETECTADAS
                # --------------------------------------

                else:

                    # Descarta a sequência incompleta.
                    sequencia.clear()

                    ultima_classe = None
                    contador_estabilidade = 0

                    self._update_state(
                        maos_detectadas=False,
                        frames=0,
                        status=(
                            "Mãos não detectadas. "
                            "Posicione suas mãos diante da câmera."
                        ),
                    )

                # --------------------------------------
                # RECONHECIMENTO DO SINAL
                # --------------------------------------

                if (
                    maos_detectadas
                    and len(sequencia) == FRAMES_PER_SEQUENCE
                ):

                    classe, confianca = prever_sinal(
                        modelo,
                        sequencia,
                    )

                    if confianca >= CONFIDENCE_THRESHOLD:

                        if classe == ultima_classe:

                            contador_estabilidade += 1

                        else:

                            ultima_classe = classe
                            contador_estabilidade = 1

                        self._update_state(
                            sinal=classe,
                            confianca=confianca,
                            status="Confirmando sinal...",
                        )

                        # ----------------------------------
                        # SINAL CONFIRMADO
                        # ----------------------------------

                        if (
                            contador_estabilidade
                            >= STABLE_PREDICTIONS
                        ):

                            # ----------------------------------
                            # CLASSE INDEFINIDO
                            # ----------------------------------

                            if classe == "indefinido":

                                self._update_state(
                                    sinal="indefinido",
                                    traducao=(
                                        "Sinal não reconhecido."
                                    ),
                                    confianca=confianca,
                                    status=(
                                        "Sinal não reconhecido. "
                                        "Tente novamente."
                                    ),
                                )

                                # Não registra no banco,
                                # não adiciona à tradução
                                # e não executa áudio.

                            # ----------------------------------
                            # SINAL VÁLIDO
                            # ----------------------------------

                            else:

                                # ----------------------------------
                                # REGISTRAR NO BANCO DE DADOS
                                # ----------------------------------

                                self._registrar_no_banco(
                                    classe,
                                    confianca,
                                )

                                # ----------------------------------
                                # ATUALIZAR TRADUÇÃO
                                # ----------------------------------

                                mensagem = adicionar_sinal(
                                    mensagem,
                                    classe,
                                )

                                self._update_state(
                                    sinal=classe,
                                    traducao=mensagem,
                                    confianca=confianca,
                                    status=(
                                        "Sinal reconhecido! "
                                        "Clique em iniciar para "
                                        "reconhecer outro."
                                    ),
                                )

                                # Executa o áudio em outra thread.
                                threading.Thread(
                                    target=falar_sinal,
                                    args=(classe,),
                                    daemon=True,
                                ).start()

                            # Encerra a captura após a confirmação.
                            break

                    else:

                        ultima_classe = None
                        contador_estabilidade = 0

                        self._update_state(
                            sinal="Sinal incerto",
                            confianca=confianca,
                            status=(
                                "Sinal não reconhecido. "
                                "Tente novamente."
                            ),
                        )

                # --------------------------------------
                # ATUALIZAR CONTADOR
                # --------------------------------------

                self._update_state(
                    frames=len(sequencia)
                )

                # --------------------------------------
                # PREPARAR IMAGEM PARA O NAVEGADOR
                # --------------------------------------

                sucesso_jpeg, buffer = cv2.imencode(
                    ".jpg",
                    frame,
                    [cv2.IMWRITE_JPEG_QUALITY, 80],
                )

                if sucesso_jpeg:

                    with self._lock:
                        self._latest_frame = buffer.tobytes()

        except Exception as erro:

            self._update_state(
                erro=str(erro),
                status="Erro no reconhecimento",
                maos_detectadas=False,
            )

        finally:

            # ------------------------------------------
            # LIBERAR RECURSOS
            # ------------------------------------------

            if detector is not None:
                detector.close()

            if camera is not None:
                camera.release()

            self._camera = None

            with self._lock:

                self._state["running"] = False
                self._state["maos_detectadas"] = False

                if self._state["status"] not in (
                    "Erro no reconhecimento",
                    (
                        "Sinal reconhecido! "
                        "Clique em iniciar para "
                        "reconhecer outro."
                    ),
                    (
                        "Sinal não reconhecido. "
                        "Tente novamente."
                    ),
                ):

                    self._state["status"] = "Parado"
