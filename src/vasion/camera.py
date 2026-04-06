import cv2
from src.utils.logger import setup_logger

logger = setup_logger()

def iniciar_camera():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        logger.error("Erro ao acessar câmera")
        print("Erro ao acessar câmera")
        return

    logger.info("Câmera iniciada com sucesso")

    while True:
        ret, frame = cap.read()

        if not ret:
            logger.error("Erro ao capturar frame")
            break

        cv2.imshow("TCC - Libras", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # tecla ESC
            logger.info("Encerrando câmera")
            break

    cap.release()
    cv2.destroyAllWindows()