# Quantidade de frames que formam uma sequência
FRAMES_PER_SEQUENCE = 60

# Quantidade máxima de mãos detectadas
MAX_NUM_HANDS = 2

# Confiança mínima para detectar uma mão
MIN_DETECTION_CONFIDENCE = 0.7

# Confiança mínima para acompanhar uma mão
MIN_TRACKING_CONFIDENCE = 0.7

# Tecla utilizada para iniciar uma coleta
START_KEY = ord("s")

# Tecla utilizada para encerrar o programa
EXIT_KEY = 27

# Pasta onde os datasets serão armazenados
DATASET_PATH = "dataset"

# Sinal que será coletado
SIGNAL_NAME = "indefinido"

# Máximo de frames consecutivos sem detectar a mão
MAX_MISSED_FRAMES = 5

# ==============================
# CONFIGURAÇÃO DOS LANDMARKS
# ==============================

LANDMARKS_PER_HAND = 21
COORDINATES_PER_LANDMARK = 3

FEATURES_PER_HAND = (
    LANDMARKS_PER_HAND *
    COORDINATES_PER_LANDMARK
)

FEATURES_PER_FRAME = (
    FEATURES_PER_HAND * 2
)