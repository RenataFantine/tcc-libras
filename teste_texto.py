from src.translation.translator import (
    identificar_sinal,
    obter_representacao_visual
)


def testar_texto(texto):

    sinal = identificar_sinal(
        texto
    )

    if not sinal:

        print(
            "Não foi encontrada uma "
            "representação para esse texto."
        )

        return

    caminho = obter_representacao_visual(
        sinal
    )

    print()
    print("=" * 50)
    print("TRADUÇÃO PORTUGUÊS → LIBRAS")
    print("=" * 50)
    print()

    print(
        f"Texto informado: {texto}"
    )

    print(
        f"Sinal identificado: {sinal}"
    )

    print(
        f"Representação visual: {caminho}"
    )

    print()


if __name__ == "__main__":

    texto = input(
        "Digite uma mensagem: "
    )

    testar_texto(texto)