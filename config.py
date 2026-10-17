from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CARPETA_ENTRADA = BASE_DIR / "entrada"
CARPETA_SALIDA = BASE_DIR / "salida"

MODELO_OLLAMA = "gemma3:4b"
COPIAR_ARCHIVOS = False