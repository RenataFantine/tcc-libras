from src.utils.logger import setup_logger

logger = setup_logger()


def normalize_landmarks(hand_landmarks):
    """
    Normaliza os landmarks utilizando
    o pulso (ponto 0) como origem.

    Retorna:
        Lista com 63 valores.
    """

    pontos = []

    base_x = hand_landmarks.landmark[0].x
    base_y = hand_landmarks.landmark[0].y
    base_z = hand_landmarks.landmark[0].z

    for landmark in hand_landmarks.landmark:

        pontos.extend([
            landmark.x - base_x,
            landmark.y - base_y,
            landmark.z - base_z
        ])

    return pontos