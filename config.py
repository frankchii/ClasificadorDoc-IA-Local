"""
config.py - Configuración central del proyecto.

Todo lo que se pueda querer ajustar (modelo, rutas, límites) vive aquí,
así el resto del código no se toca para cambiar el comportamiento.
"""
import os
from pathlib import Path

# --- Rutas (relativas a la carpeta del proyecto: funcionan en cualquier PC) ---
BASE_DIR = Path(__file__).resolve().parent
CARPETA_ENTRADA = BASE_DIR / "entrada"   # el usuario deja aquí sus documentos
CARPETA_SALIDA = BASE_DIR / "salida"     # aquí se organizan los archivos y se guarda el informe

# --- Conexión con Ollama ---
OLLAMA_HOST = "http://localhost:11434"
# Se puede cambiar sin editar el código:  set MODELO_OLLAMA=gemma2   (cmd)
MODELO = os.getenv("MODELO_OLLAMA", "llama3:8b")
TIMEOUT_SEG = 300        # la primera llamada es lenta: Ollama carga el modelo en RAM
MAX_REINTENTOS = 3       # intentos si el JSON llega mal formado o no valida
NUM_CTX = 4096           # ventana de contexto que se pide al modelo (tokens)

# --- PDF escaneados (sin texto): se analizan como imagen con un modelo de visión ---
# Requiere:  ollama pull gemma3:4b   y   python -m pip install pymupdf
MODELO_VISION = os.getenv("MODELO_VISION_OLLAMA", "gemma3:4b")
PAGINAS_VISION = 2       # cuántas páginas iniciales se envían (más páginas = más lento)

# --- Extracción de texto ---
# 6000 caracteres ~ 1500-2000 tokens: caben de sobra en NUM_CTX junto con el prompt.
MAX_CARACTERES = 6000
EXTENSIONES_SOPORTADAS = {".pdf", ".docx", ".txt"}

# --- Organización de archivos ---
# False = los archivos se MUEVEN a salida/<Categoria>/ (la carpeta de entrada queda vacía).
# True  = se COPIAN (útil para pruebas: los originales no se tocan).
COPIAR_EN_VEZ_DE_MOVER = False

# --- Informe ---
FORMATO_INFORME = "excel"            # "excel", "word" o "ambos"
NOMBRE_INFORME = "informe_clasificacion"
