import cv2
import mediapipe as mp

from src.utils.logger import setup_logger
from src.vision.hands import HandDetector
from src.vision.landmarks import extract_landmarks
from src.vision.normalizer import normalize_landmarks

logger = setup_logger()

mp_drawing = mp.solutions.drawing_utils


def iniciar_camera():

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        logger.error("Não foi possível abrir a câmera.")
        return

    detector = HandDetector(max_num_hands=2)

    logger.info("Câmera iniciada.")

    while True:

        ret, frame = cap.read()

        if not ret:
            logger.error("Erro ao capturar frame.")
            break

        frame = cv2.flip(frame, 1)

        resultado = detector.detect(frame)

        if resultado and resultado.multi_hand_landmarks:

            for hand_landmarks in resultado.multi_hand_landmarks:

                # Desenha os 21 pontos na tela
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp.solutions.hands.HAND_CONNECTIONS
                )

                # Extrai os landmarks originais
                pontos = extract_landmarks(hand_landmarks)

                # Normaliza os landmarks usando o pulso como referência
                pontos_normalizados = normalize_landmarks(hand_landmarks)

                print(f"Valores originais: {len(pontos)}")
                print(
                    f"Valores normalizados: "
                    f"{len(pontos_normalizados)}"
                )

        cv2.imshow("TCC - Libras", frame)

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == 27:  # ESC
            break

    detector.close()
    cap.release()
    cv2.destroyAllWindows()

    logger.info("Câmera encerrada.")


if __name__ == "__main__":
    iniciar_camera()