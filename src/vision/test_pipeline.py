import cv2

from src.vision.hands import HandDetector
from src.vision.landmarks import (
    extract_landmarks,
    extract_normalized_hands
)
from src.vision.normalizer import normalize_landmarks


def testar_pipeline():

    # =====================================================
    # CÂMERA
    # =====================================================

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():

        print("❌ Não foi possível abrir a câmera.")

        return

    # =====================================================
    # DETECTOR
    # =====================================================

    detector = HandDetector(
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )

    print("=" * 70)
    print(" TESTE COMPLETO DO PIPELINE")
    print("=" * 70)
    print()
    print("Coloque uma ou duas mãos na câmera.")
    print("Pressione ESC para sair.")
    print()

    teste_realizado = False

    # =====================================================
    # LOOP PRINCIPAL
    # =====================================================

    while True:

        ret, frame = cap.read()

        if not ret:

            print("❌ Erro ao capturar frame.")

            break

        frame = cv2.flip(
            frame,
            1
        )

        # =================================================
        # DETECÇÃO
        # =================================================

        resultado = detector.detect(
            frame
        )

        if (
            resultado
            and resultado.multi_hand_landmarks
        ):

            print()
            print("-" * 70)

            quantidade_maos = len(
                resultado.multi_hand_landmarks
            )

            print(
                "MÃOS DETECTADAS:",
                quantidade_maos
            )

            print(
                "HANDEDNESS DISPONÍVEL:",
                bool(resultado.multi_handedness)
            )

            # =================================================
            # TESTE INDIVIDUAL DE CADA MÃO
            # =================================================

            for indice, hand_landmarks in enumerate(
                resultado.multi_hand_landmarks
            ):

                print()
                print(
                    f"--- MÃO {indice + 1} ---"
                )

                # ---------------------------------------------
                # LANDMARK BRUTO
                # ---------------------------------------------

                ponto_bruto = (
                    hand_landmarks.landmark[1]
                )

                print(
                    "Landmark bruto p1:",
                    ponto_bruto.x,
                    ponto_bruto.y,
                    ponto_bruto.z
                )

                # ---------------------------------------------
                # EXTRAÇÃO
                # ---------------------------------------------

                pontos = extract_landmarks(
                    hand_landmarks
                )

                print(
                    "Quantidade extract_landmarks:",
                    len(pontos)
                )

                print(
                    "Primeiros valores:",
                    pontos[:9]
                )

                # ---------------------------------------------
                # NORMALIZAÇÃO
                # ---------------------------------------------

                pontos_normalizados = (
                    normalize_landmarks(
                        hand_landmarks
                    )
                )

                print(
                    "Quantidade normalizada:",
                    len(pontos_normalizados)
                )

                print(
                    "Primeiros valores normalizados:",
                    pontos_normalizados[:9]
                )

            # =================================================
            # HANDEDNESS
            # =================================================

            print()
            print("--- HANDEDNESS ---")

            if resultado.multi_handedness:

                for indice, handedness in enumerate(
                    resultado.multi_handedness
                ):

                    classificacao = (
                        handedness.classification[0]
                    )

                    label = classificacao.label
                    score = classificacao.score

                    print(
                        f"Mão {indice + 1}:"
                    )

                    print(
                        f"  label = {repr(label)}"
                    )

                    print(
                        f"  score = {score:.3f}"
                    )

            else:

                print(
                    "⚠️ Nenhuma informação de handedness."
                )

            # =================================================
            # EXTRAÇÃO DAS DUAS MÃOS
            # =================================================

            pontos_duas_maos = (
                extract_normalized_hands(
                    resultado
                )
            )

            print()
            print(
                "--- EXTRACT NORMALIZED HANDS ---"
            )

            print(
                "Quantidade:",
                len(pontos_duas_maos)
            )

            print(
                "Primeiros 12 valores:",
                pontos_duas_maos[:12]
            )

            # =================================================
            # VERIFICAÇÃO DAS 126 FEATURES
            # =================================================

            if len(pontos_duas_maos) == 126:

                print(
                    "✅ 126 FEATURES CONFIRMADAS."
                )

            else:

                print(
                    "❌ ERRO: esperado 126 "
                    f"features, recebido "
                    f"{len(pontos_duas_maos)}."
                )

            # =================================================
            # SEPARAÇÃO ESQUERDA / DIREITA
            # =================================================

            esquerda = pontos_duas_maos[:63]

            direita = pontos_duas_maos[63:]

            quantidade_esquerda = sum(
                valor != 0
                for valor in esquerda
            )

            quantidade_direita = sum(
                valor != 0
                for valor in direita
            )

            print()
            print(
                "--- DISTRIBUIÇÃO DAS FEATURES ---"
            )

            print(
                "Esquerda:",
                quantidade_esquerda,
                "/ 63 valores diferentes de zero"
            )

            print(
                "Direita:",
                quantidade_direita,
                "/ 63 valores diferentes de zero"
            )

            # =================================================
            # DIAGNÓSTICO
            # =================================================

            if (
                quantidade_esquerda == 0
                and quantidade_direita == 0
            ):

                print()
                print(
                    "❌ PROBLEMA:"
                )

                print(
                    "Nenhuma das duas mãos "
                    "possui valores."
                )

            elif (
                quantidade_esquerda > 0
                and quantidade_direita == 0
            ):

                print()
                print(
                    "✅ Mão esquerda possui dados."
                )

                print(
                    "ℹ️ Mão direita está zerada "
                    "porque não foi detectada."
                )

            elif (
                quantidade_esquerda == 0
                and quantidade_direita > 0
            ):

                print()
                print(
                    "ℹ️ Mão esquerda está zerada "
                    "porque não foi detectada."
                )

                print(
                    "✅ Mão direita possui dados."
                )

            else:

                print()
                print(
                    "✅ AS DUAS MÃOS POSSUEM DADOS."
                )

            print()
            print("-" * 70)

            teste_realizado = True

        else:

            print(
                "Nenhuma mão detectada."
            )

        # =================================================
        # EXIBIÇÃO DA CÂMERA
        # =================================================

        cv2.imshow(
            "Teste do Pipeline",
            frame
        )

        # =================================================
        # TECLADO
        # =================================================

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == 27:

            break

        # =================================================
        # CONTROLE DO TESTE
        # =================================================

        if teste_realizado:

            print()
            print(
                "✅ Teste realizado."
            )

            print(
                "Pressione ESC para encerrar."
            )

            teste_realizado = False

    # =====================================================
    # ENCERRAMENTO
    # =====================================================

    detector.close()

    cap.release()

    cv2.destroyAllWindows()

    print()
    print(
        "Teste encerrado."
    )


if __name__ == "__main__":
    testar_pipeline()