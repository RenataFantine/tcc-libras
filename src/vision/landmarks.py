from src.utils.logger import setup_logger
from src.vision.normalizer import normalize_landmarks


logger = setup_logger()


def extract_landmarks(hand_landmarks):
    """
    Extrai os 21 landmarks de uma mão.

    Retorna:
        Lista com 63 valores:
        x, y e z de cada landmark.
    """

    pontos = []

    for landmark in hand_landmarks.landmark:

        pontos.extend([
            landmark.x,
            landmark.y,
            landmark.z
        ])

    return pontos


def extract_both_hands(resultado):
    """
    Extrai os landmarks das mãos esquerda e direita.

    Cada mão possui 63 valores.

    Retorna:
        left_hand:
            63 valores ou None

        right_hand:
            63 valores ou None
    """

    left_hand = None
    right_hand = None

    if resultado is None:
        return left_hand, right_hand

    if not resultado.multi_hand_landmarks:
        return left_hand, right_hand

    if not resultado.multi_handedness:
        return left_hand, right_hand

    for hand_landmarks, handedness in zip(
        resultado.multi_hand_landmarks,
        resultado.multi_handedness
    ):

        classificacao = handedness.classification[0]

        label = classificacao.label.strip()

        pontos = extract_landmarks(
            hand_landmarks
        )

        if label == "Left":

            left_hand = pontos

        elif label == "Right":

            right_hand = pontos

    return left_hand, right_hand


def extract_normalized_hands(resultado):
    """
    Extrai e normaliza as duas mãos.

    Cada mão possui 63 valores.

    Retorna sempre:

        126 valores

        63 → mão esquerda
        63 → mão direita

    Quando uma mão não está presente,
    seus valores são preenchidos com zero.
    """

    zeros = [0.0] * 63

    left_hand = zeros.copy()
    right_hand = zeros.copy()

    if resultado is None:
        return left_hand + right_hand

    if not resultado.multi_hand_landmarks:
        return left_hand + right_hand

    if not resultado.multi_handedness:
        return left_hand + right_hand

    for hand_landmarks, handedness in zip(
        resultado.multi_hand_landmarks,
        resultado.multi_handedness
    ):

        classificacao = handedness.classification[0]

        label = classificacao.label.strip()

        pontos_normalizados = normalize_landmarks(
            hand_landmarks
        )

        logger.debug(
            f"Mão detectada: {label} | "
            f"Confiança: {classificacao.score:.3f}"
        )

        if label == "Left":

            left_hand = pontos_normalizados

        elif label == "Right":

            right_hand = pontos_normalizados

        else:

            logger.warning(
                f"Lado de mão desconhecido: "
                f"'{label}'"
            )

    return left_hand + right_hand