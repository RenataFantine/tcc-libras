import cv2

from src.vision.hands import HandDetector
from src.vision.landmarks import extract_normalized_hands


def testar_landmarks():

    # =====================================================
    # CÂMERA
    # =====================================================

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():

        print(
            "❌ Não foi possível abrir a câmera."
        )

        return

    # =====================================================
    # DETECTOR
    # =====================================================

    detector = HandDetector(
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )

    print("=" * 60)
    print(" TESTE DE LANDMARKS - DUAS MÃOS")
    print("=" * 60)
    print()
    print("Coloque uma ou duas mãos na câmera.")
    print("Retire as mãos para testar a detecção.")
    print("Pressione ESC para sair.")
    print()

    # =====================================================
    # LOOP
    # =====================================================

    while True:

        ret, frame = cap.read()

        if not ret:

            print(
                "❌ Erro ao capturar frame."
            )

            break

        # Espelha a imagem
        frame = cv2.flip(
            frame,
            1
        )

        # Detecta as mãos
        resultado = detector.detect(
            frame
        )

        # =================================================
        # PROCESSAMENTO
        # =================================================

        if (
            resultado
            and resultado.multi_hand_landmarks
        ):

            quantidade_maos = len(
                resultado.multi_hand_landmarks
            )

        else:

            quantidade_maos = 0

        # Extrai os 126 valores
        pontos = extract_normalized_hands(
            resultado
        )

        quantidade_features = len(
            pontos
        )

        # =================================================
        # RESULTADO
        # =================================================

        print(
            f"Mãos detectadas: "
            f"{quantidade_maos} | "
            f"Features: "
            f"{quantidade_features}"
        )

        # =================================================
        # VALIDAÇÃO
        # =================================================

        if quantidade_features == 126:

            print(
                "✅ TESTE OK - "
                "126 features"
            )

        else:

            print(
                "❌ ERRO - "
                "esperado 126, "
                f"recebido "
                f"{quantidade_features}"
            )

        # =================================================
        # TEXTO NA CÂMERA
        # =================================================

        texto = (
            f"Maos detectadas: "
            f"{quantidade_maos}"
        )

        cv2.putText(
            frame,
            texto,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.imshow(
            "Teste de Landmarks",
            frame
        )

        # =================================================
        # TECLADO
        # =================================================

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == 27:

            break

    # =====================================================
    # ENCERRAMENTO
    # =====================================================

    detector.close()

    cap.release()

    cv2.destroyAllWindows()

    print()
    print("Teste encerrado.")


if __name__ == "__main__":
    testar_landmarks()