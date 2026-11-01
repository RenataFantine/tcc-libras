# =========================
# TRADUTOR DE LIBRAS
# =========================


# =========================
# DICIONÁRIO DE TRADUÇÃO
# =========================

TRADUCOES = {
    "oi": "Olá!",
    "ajuda": "Preciso de ajuda.",
    "obrigado": "Obrigado."
}


# =========================
# ENTRADAS DO OUVINTE
# =========================

ENTRADAS_TEXTO = {
    "oi": "oi",
    "olá": "oi",
    "ola": "oi",

    "ajuda": "ajuda",
    "preciso de ajuda": "ajuda",

    "obrigado": "obrigado",
    "obrigada": "obrigado"
}


# =========================
# REPRESENTAÇÕES VISUAIS
# =========================

REPRESENTACOES_VISUAIS = {
    "oi": "sinais/oi/oi.mp4",
    "ajuda": "sinais/ajuda/ajuda.mp4",
    "obrigado": "sinais/obrigado/obrigado.mp4"
}


# =========================
# TRADUZIR SINAL
# =========================

def traduzir_sinal(sinal):
    """
    Retorna a tradução textual de um sinal.
    """

    if not sinal:
        return ""

    sinal = sinal.lower().strip()

    return TRADUCOES.get(
        sinal,
        "Tradução indisponível."
    )


# =========================
# IDENTIFICAR SINAL PELO TEXTO
# =========================

def identificar_sinal(texto):
    """
    Identifica o sinal correspondente
    ao texto informado pelo ouvinte.
    """

    if not texto:
        return None

    texto = texto.lower().strip()

    return ENTRADAS_TEXTO.get(
        texto
    )


# =========================
# REPRESENTAÇÃO VISUAL
# =========================

def obter_representacao_visual(sinal):
    """
    Retorna o caminho da representação
    visual correspondente ao sinal.
    """

    if not sinal:
        return None

    sinal = sinal.lower().strip()

    return REPRESENTACOES_VISUAIS.get(
        sinal
    )


# =========================
# CONSTRUÇÃO DA FRASE
# =========================

def adicionar_sinal(frase, sinal):
    """
    Adiciona a tradução de um sinal
    à frase atual.
    """

    traducao = traduzir_sinal(
        sinal
    )

    if (
        not traducao
        or traducao == "Tradução indisponível."
    ):
        return frase

    if not frase:
        return traducao

    return f"{frase} {traducao}"