import os
import tempfile
import time

import pygame
from gtts import gTTS

from src.utils.logger import setup_logger


logger = setup_logger()


# =========================================================
# TRADUÇÃO DOS SINAIS
# =========================================================

TEXTOS_SINAIS = {
    "oi": "Olá!",
    "ajuda": "Preciso de ajuda.",
    "obrigado": "Obrigado."
}


# =========================================================
# INICIALIZAÇÃO DO ÁUDIO
# =========================================================

pygame.mixer.init()


# =========================================================
# CONVERSÃO DE TEXTO PARA ÁUDIO
# =========================================================

def falar(texto):
    """
    Converte um texto em áudio e reproduz dentro do sistema.
    """

    if not texto:
        logger.warning(
            "Nenhum texto foi informado para reprodução."
        )

        return

    caminho_audio = None

    try:

        # -------------------------------------------------
        # Cria o arquivo temporário
        # -------------------------------------------------

        with tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        ) as arquivo:

            caminho_audio = arquivo.name

        # -------------------------------------------------
        # Gera o áudio
        # -------------------------------------------------

        tts = gTTS(
            text=texto,
            lang="pt-br",
            slow=False
        )

        tts.save(
            caminho_audio
        )

        logger.info(
            f"Áudio gerado: {texto}"
        )

        # -------------------------------------------------
        # Reprodução interna
        # -------------------------------------------------

        pygame.mixer.music.load(
            caminho_audio
        )

        pygame.mixer.music.play()

        # Aguarda o término do áudio.
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        logger.info(
            "Reprodução do áudio finalizada."
        )

    except Exception as erro:

        logger.error(
            f"Erro ao reproduzir áudio: {erro}"
        )

    finally:

        # -------------------------------------------------
        # Remove o arquivo temporário
        # -------------------------------------------------

        if caminho_audio and os.path.exists(caminho_audio):

            try:
                os.remove(caminho_audio)

            except PermissionError:
                logger.warning(
                    "Não foi possível remover o arquivo de áudio temporário."
                )


# =========================================================
# CONVERSÃO DO SINAL
# =========================================================

def falar_sinal(sinal):
    """
    Converte o nome do sinal reconhecido
    em uma frase e reproduz o áudio.
    """

    if not sinal:
        return

    sinal = sinal.lower().strip()

    texto = TEXTOS_SINAIS.get(
        sinal
    )

    if texto is None:

        logger.warning(
            f"Sinal sem tradução de áudio: {sinal}"
        )

        return

    falar(
        texto
    )


# =========================================================
# TESTE
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 50)
    print("TESTE DO SISTEMA DE ÁUDIO")
    print("=" * 50)
    print()

    falar_sinal(
        "oi"
    )

    print(
        "Teste de áudio finalizado."
    )