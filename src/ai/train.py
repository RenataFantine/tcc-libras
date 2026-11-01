
import os
import json
import numpy as np

from tensorflow.keras.callbacks import (
    EarlyStopping,
    ModelCheckpoint
)

from src.dataset.prepare import preparar_dataset
from src.ai.model import criar_modelo
from src.utils.logger import setup_logger


logger = setup_logger()


# =========================================================
# CONFIGURAÇÕES
# =========================================================

EPOCHS = 100
BATCH_SIZE = 4
VALIDATION_RATIO = 0.20

# Não sobrescreve o modelo antigo.
MODEL_PATH = "models/libras_model_teste.keras"

# Arquivo com a ordem das classes utilizadas no treinamento.
CLASSES_PATH = "models/libras_model_teste_classes.json"

RANDOM_SEED = 42


# =========================================================
# DIVISÃO TREINO / VALIDAÇÃO
# =========================================================

def separar_validacao(
    X,
    y,
    proporcao=VALIDATION_RATIO
):
    """
    Divide o conjunto de treinamento em treino e validação,
    mantendo a proporção entre as classes.
    """

    np.random.seed(RANDOM_SEED)

    X_treino = []
    y_treino = []

    X_validacao = []
    y_validacao = []

    classes = np.unique(y)

    for classe in classes:

        indices = np.where(y == classe)[0]

        np.random.shuffle(indices)

        quantidade_validacao = max(
            1,
            int(len(indices) * proporcao)
        )

        indices_validacao = indices[:quantidade_validacao]
        indices_treino = indices[quantidade_validacao:]

        for indice in indices_treino:
            X_treino.append(X[indice])
            y_treino.append(y[indice])

        for indice in indices_validacao:
            X_validacao.append(X[indice])
            y_validacao.append(y[indice])

    X_treino = np.array(X_treino, dtype=np.float32)
    y_treino = np.array(y_treino, dtype=np.int32)

    X_validacao = np.array(X_validacao, dtype=np.float32)
    y_validacao = np.array(y_validacao, dtype=np.int32)

    # Embaralha novamente os conjuntos.
    indices_treino = np.random.permutation(len(X_treino))
    indices_validacao = np.random.permutation(len(X_validacao))

    X_treino = X_treino[indices_treino]
    y_treino = y_treino[indices_treino]

    X_validacao = X_validacao[indices_validacao]
    y_validacao = y_validacao[indices_validacao]

    return (
        X_treino,
        X_validacao,
        y_treino,
        y_validacao
    )


# =========================================================
# MATRIZ DE CONFUSÃO
# =========================================================

def mostrar_matriz_confusao(
    y_real,
    y_predito,
    nomes_classes
):
    """
    Linhas = classe real
    Colunas = classe prevista
    """

    quantidade_classes = len(nomes_classes)

    matriz = np.zeros(
        (quantidade_classes, quantidade_classes),
        dtype=np.int32
    )

    for real, predito in zip(y_real, y_predito):
        matriz[real, predito] += 1

    print()
    print("=" * 70)
    print("MATRIZ DE CONFUSÃO")
    print("=" * 70)
    print()

    cabecalho = "Real \\ Previsto"

    print(f"{cabecalho:<20}", end="")

    for nome in nomes_classes:
        print(f"{nome:<15}", end="")

    print()
    print("-" * 80)

    for indice, nome in enumerate(nomes_classes):

        print(f"{nome:<20}", end="")

        for coluna in range(quantidade_classes):
            print(f"{matriz[indice, coluna]:<15}", end="")

        print()

    print()

    return matriz


# =========================================================
# RESULTADOS POR CLASSE
# =========================================================

def mostrar_resultados_por_classe(
    matriz,
    nomes_classes
):
    """
    Mostra acertos, erros e taxa de acerto de cada classe.
    """

    print("=" * 70)
    print("RESULTADO POR CLASSE")
    print("=" * 70)
    print()

    for indice, nome in enumerate(nomes_classes):

        total = np.sum(matriz[indice])
        acertos = matriz[indice, indice]
        erros = total - acertos

        if total > 0:
            taxa = (acertos / total) * 100
        else:
            taxa = 0

        print(
            f"{nome:<12} "
            f"Total: {total:<3} "
            f"Acertos: {acertos:<3} "
            f"Erros: {erros:<3} "
            f"Taxa: {taxa:.2f}%"
        )

    print()


# =========================================================
# DISTRIBUIÇÃO DAS CLASSES
# =========================================================

def mostrar_distribuicao(
    titulo,
    y,
    nomes_classes
):
    print(titulo)
    print()

    for indice, nome in enumerate(nomes_classes):

        quantidade = np.sum(y == indice)

        print(
            f"  [{indice}] {nome:<12}: "
            f"{quantidade} amostras"
        )

    print()


# =========================================================
# SALVAR CLASSES
# =========================================================

def salvar_classes(nomes_classes):

    os.makedirs(
        os.path.dirname(CLASSES_PATH),
        exist_ok=True
    )

    dados = {
        "classes": nomes_classes,
        "quantidade_classes": len(nomes_classes)
    }

    with open(
        CLASSES_PATH,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=4
        )

    logger.info(
        f"Classes salvas em: {CLASSES_PATH}"
    )


# =========================================================
# TREINAMENTO
# =========================================================

def treinar_modelo():

    np.random.seed(RANDOM_SEED)

    # =====================================================
    # PREPARAÇÃO DO DATASET
    # =====================================================

    (
        X_train,
        X_test,
        y_train,
        y_test,
        nomes_classes
    ) = preparar_dataset()

    # =====================================================
    # VERIFICAÇÕES
    # =====================================================

    if X_train is None or X_test is None:

        logger.error(
            "Dataset não pôde ser preparado."
        )

        return

    if len(X_train) == 0 or len(X_test) == 0:

        logger.error(
            "Conjunto de treinamento ou teste vazio."
        )

        return

    if len(nomes_classes) != 4:

        logger.error(
            f"Esperadas 4 classes, encontradas: "
            f"{len(nomes_classes)}"
        )

        return

    if len(np.unique(y_train)) != 4:

        logger.error(
            "Nem todas as classes estão presentes "
            "no conjunto de treinamento."
        )

        return

    if X_train.ndim != 3 or X_train.shape[2] != 126:

        logger.error(
            f"Formato inesperado para X_train: "
            f"{X_train.shape}"
        )

        return

    print()
    print("=" * 70)
    print("CLASSES DO TREINAMENTO")
    print("=" * 70)

    for indice, nome in enumerate(nomes_classes):
        print(f"[{indice}] {nome}")

    print()

    # =====================================================
    # DIVISÃO TREINO / VALIDAÇÃO
    # =====================================================

    (
        X_treino,
        X_validacao,
        y_treino,
        y_validacao
    ) = separar_validacao(
        X_train,
        y_train
    )

    if len(X_validacao) == 0:

        logger.error(
            "Conjunto de validação vazio."
        )

        return

    # =====================================================
    # INFORMAÇÕES DOS DADOS
    # =====================================================

    print()
    print("=" * 70)
    print("DIVISÃO DO DATASET")
    print("=" * 70)
    print()

    print(f"Treinamento : {len(X_treino)} amostras")
    print(f"Validação   : {len(X_validacao)} amostras")
    print(f"Teste final : {len(X_test)} amostras")

    print()

    mostrar_distribuicao(
        "Distribuição do treinamento:",
        y_treino,
        nomes_classes
    )

    mostrar_distribuicao(
        "Distribuição da validação:",
        y_validacao,
        nomes_classes
    )

    mostrar_distribuicao(
        "Distribuição do teste:",
        y_test,
        nomes_classes
    )

    # =====================================================
    # DIRETÓRIO DO MODELO
    # =====================================================

    os.makedirs("models", exist_ok=True)

    # =====================================================
    # CRIAÇÃO DO MODELO
    # =====================================================

    modelo = criar_modelo(
        frames=X_treino.shape[1],
        features=X_treino.shape[2],
        quantidade_classes=len(nomes_classes)
    )

    # =====================================================
    # ARQUITETURA
    # =====================================================

    print()
    print("=" * 70)
    print("ARQUITETURA DO MODELO")
    print("=" * 70)
    print()

    modelo.summary()

    # =====================================================
    # CALLBACKS
    # =====================================================

    early_stopping = EarlyStopping(
        monitor="val_loss",
        patience=15,
        restore_best_weights=True,
        verbose=1
    )

    checkpoint = ModelCheckpoint(
        filepath=MODEL_PATH,
        monitor="val_accuracy",
        save_best_only=True,
        mode="max",
        verbose=1
    )

    # =====================================================
    # TREINAMENTO
    # =====================================================

    print()
    print("=" * 70)
    print("INICIANDO TREINAMENTO")
    print("=" * 70)
    print()

    historico = modelo.fit(

        X_treino,
        y_treino,

        validation_data=(
            X_validacao,
            y_validacao
        ),

        epochs=EPOCHS,

        batch_size=BATCH_SIZE,

        callbacks=[
            early_stopping,
            checkpoint
        ],

        shuffle=True,

        verbose=1
    )

    # =====================================================
    # TESTE FINAL
    # =====================================================

    print()
    print("=" * 70)
    print("TESTE FINAL")
    print("=" * 70)
    print()

    perda, acuracia = modelo.evaluate(
        X_test,
        y_test,
        verbose=0
    )

    print(f"Loss: {perda:.4f}")
    print(f"Acurácia: {acuracia * 100:.2f}%")

    # =====================================================
    # PREVISÕES
    # =====================================================

    probabilidades = modelo.predict(
        X_test,
        verbose=0
    )

    y_predito = np.argmax(
        probabilidades,
        axis=1
    )

    # =====================================================
    # MATRIZ DE CONFUSÃO
    # =====================================================

    matriz = mostrar_matriz_confusao(
        y_test,
        y_predito,
        nomes_classes
    )

    # =====================================================
    # RESULTADO POR CLASSE
    # =====================================================

    mostrar_resultados_por_classe(
        matriz,
        nomes_classes
    )

    # =====================================================
    # SALVAR ORDEM DAS CLASSES
    # =====================================================

    salvar_classes(nomes_classes)

    # =====================================================
    # RESULTADO FINAL
    # =====================================================

    print("=" * 70)
    print("ARQUIVOS GERADOS")
    print("=" * 70)
    print()

    print(f"Modelo: {MODEL_PATH}")
    print(f"Classes: {CLASSES_PATH}")

    print()
    print("=" * 70)
    print("TREINAMENTO FINALIZADO!")
    print("=" * 70)
    print()

    return (
        modelo,
        historico,
        nomes_classes
    )


# =========================================================
# EXECUÇÃO
# =========================================================

if __name__ == "__main__":

    treinar_modelo()
