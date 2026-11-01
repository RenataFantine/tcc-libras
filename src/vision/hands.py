import cv2
import mediapipe as mp

from src.utils.logger import setup_logger

logger = setup_logger()

mp_hands = mp.solutions.hands


class HandDetector:
    def __init__(
        self,
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    ):
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def detect(self, frame):
        """
        Recebe um frame BGR do OpenCV
        e retorna o resultado do MediaPipe.
        """

        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            resultado = self.hands.process(rgb_frame)

            return resultado

        except Exception as erro:
            logger.error(f"Erro na detecção das mãos: {erro}")
            return None

    def close(self):
        self.hands.close()