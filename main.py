from src.utils.logger import setup_logger
from src.vasion.camera import iniciar_camera

logger = setup_logger()

def main():
    logger.info("Sistema iniciado ")

    try:
        iniciar_camera()
    except Exception as e:
        logger.error(f"Erro geral: {e}")

if __name__ == "__main__":
    main()