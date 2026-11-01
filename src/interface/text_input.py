import os
import tkinter as tk
from tkinter import messagebox

from src.translation.translator import (
    identificar_sinal,
    obter_representacao_visual
)

from src.visual.player import reproduzir_video


# =========================
# CORES DA INTERFACE
# =========================

AZUL_ESCURO = "#0B1F33"
AZUL = "#164A70"
AZUL_CLARO = "#DCEEFF"
BRANCO = "#FFFFFF"
CINZA = "#607080"


# =========================
# PROCESSAMENTO DO TEXTO
# =========================

def processar_texto():
    texto = entrada_texto.get().strip()

    if not texto:
        messagebox.showwarning(
            "Atenção",
            "Digite uma mensagem antes de continuar."
        )
        return

    sinal = identificar_sinal(texto)

    if not sinal:
        messagebox.showwarning(
            "Sinal não encontrado",
            "Ainda não existe uma representação em Libras para esse texto."
        )
        return

    caminho_video = obter_representacao_visual(sinal)

    if not caminho_video:
        messagebox.showwarning(
            "Vídeo não encontrado",
            f"Não existe um vídeo cadastrado para o sinal '{sinal}'."
        )
        return

    if not os.path.exists(caminho_video):
        messagebox.showerror(
            "Erro",
            f"O arquivo do vídeo não foi encontrado:\n{caminho_video}"
        )
        return

    status.config(
        text=f"Sinal identificado: {sinal.upper()}",
        fg=AZUL
    )

    reproduzir_video(caminho_video)


# =========================
# LIMPAR CAMPO
# =========================

def limpar_texto():
    entrada_texto.delete(0, tk.END)
    status.config(
        text="Digite uma mensagem para continuar.",
        fg=CINZA
    )


# =========================
# JANELA PRINCIPAL
# =========================

janela = tk.Tk()

janela.title("Totem Inteligente — Libras")
janela.geometry("800x500")
janela.configure(bg=BRANCO)
janela.resizable(False, False)


# =========================
# CABEÇALHO
# =========================

cabecalho = tk.Frame(
    janela,
    bg=AZUL_ESCURO,
    height=100
)

cabecalho.pack(fill="x")
cabecalho.pack_propagate(False)


titulo = tk.Label(
    cabecalho,
    text="TOTEM INTELIGENTE",
    font=("Arial", 24, "bold"),
    bg=AZUL_ESCURO,
    fg=BRANCO
)

titulo.pack(pady=(20, 2))


subtitulo = tk.Label(
    cabecalho,
    text="Atendimento em Libras",
    font=("Arial", 13),
    bg=AZUL_ESCURO,
    fg=AZUL_CLARO
)

subtitulo.pack()


# =========================
# ÁREA PRINCIPAL
# =========================

conteudo = tk.Frame(
    janela,
    bg=BRANCO
)

conteudo.pack(
    fill="both",
    expand=True,
    padx=80,
    pady=40
)


orientacao = tk.Label(
    conteudo,
    text="Digite uma mensagem para a pessoa surda:",
    font=("Arial", 15, "bold"),
    bg=BRANCO,
    fg=AZUL_ESCURO
)

orientacao.pack(anchor="w")


# =========================
# CAMPO DE TEXTO
# =========================

entrada_texto = tk.Entry(
    conteudo,
    font=("Arial", 16),
    bg=AZUL_CLARO,
    fg=AZUL_ESCURO,
    relief="flat"
)

entrada_texto.pack(
    fill="x",
    ipady=14,
    pady=(12, 20)
)

entrada_texto.focus()


# =========================
# BOTÕES
# =========================

botoes = tk.Frame(
    conteudo,
    bg=BRANCO
)

botoes.pack()


botao_libras = tk.Button(
    botoes,
    text="MOSTRAR EM LIBRAS",
    command=processar_texto,
    font=("Arial", 13, "bold"),
    bg=AZUL,
    fg=BRANCO,
    activebackground=AZUL_ESCURO,
    activeforeground=BRANCO,
    relief="flat",
    padx=25,
    pady=12,
    cursor="hand2"
)

botao_libras.pack(side="left", padx=5)


botao_limpar = tk.Button(
    botoes,
    text="LIMPAR",
    command=limpar_texto,
    font=("Arial", 13),
    bg=AZUL_CLARO,
    fg=AZUL_ESCURO,
    relief="flat",
    padx=25,
    pady=12,
    cursor="hand2"
)

botao_limpar.pack(side="left", padx=5)


# =========================
# STATUS
# =========================

status = tk.Label(
    conteudo,
    text="Digite uma mensagem para continuar.",
    font=("Arial", 11),
    bg=BRANCO,
    fg=CINZA
)

status.pack(pady=30)


# =========================
# TECLA ENTER
# =========================

janela.bind(
    "<Return>",
    lambda evento: processar_texto()
)


# =========================
# INICIAR INTERFACE
# =========================

janela.mainloop()