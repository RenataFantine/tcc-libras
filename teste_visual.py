import cv2

from src.translation.translator import (
    obter_representacao_visual
)


def testar_representacao(sinal):
    """
    Testa a representação visual de um sinal.
    """

    caminho_video = obter_representacao_visual(
        sinal
    )

    if not caminho_video:

        print(
            "Nenhuma representação encontrada."
        )

        return

    print(
        f"Vídeo encontrado: {caminho_video}"
    )

    video = cv2.VideoCapture(
        caminho_video
    )

    if not video.isOpened():

        print(
            "Não foi possível abrir o vídeo."
        )

        return

    print(
        "Vídeo aberto com sucesso."
    )

    print(
        "Pressione ESC para fechar."
    )

    while True:

        sucesso, frame = video.read()

        if not sucesso:

            # Volta para o início
            video.set(
                cv2.CAP_PROP_POS_FRAMES,
                0
            )

            continue

        cv2.imshow(
            "Representacao em Libras - Oi",
            frame
        )

        tecla = cv2.waitKey(30) & 0xFF

        if tecla == 27:
            break

    video.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":

    testar_representacao("oi")