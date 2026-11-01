import cv2

from src.utils.logger import setup_logger


logger = setup_logger()


def reproduzir_video(caminho_video):
    """
    Reproduz um vídeo de Libras uma única vez.
    Pressione ESC para interromper a reprodução.
    """

    video = cv2.VideoCapture(caminho_video)

    if not video.isOpened():
        logger.error(f"Não foi possível abrir o vídeo: {caminho_video}")
        return

    logger.info(f"Reproduzindo vídeo: {caminho_video}")

    while True:
        sucesso, frame = video.read()

        # Encerra quando o vídeo chegar ao final.
        if not sucesso:
            break

        cv2.imshow("Representacao em Libras", frame)

        # ESC encerra a reprodução.
        tecla = cv2.waitKey(30) & 0xFF

        if tecla == 27:
            break

    video.release()
    cv2.destroyAllWindows()

    logger.info("Reprodução do vídeo encerrada.")