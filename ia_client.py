"""
ia_client.py - Conexión con Ollama (IA local) y validación de su respuesta.

Estrategia de fiabilidad en tres capas:
  1. El prompt de sistema exige responder solo con JSON.
  2. Se pasa el JSON Schema de Pydantic en el parámetro `format` de Ollama
     (salida estructurada: el servidor restringe la generación a ese esquema).
  3. Pydantic valida el resultado; si falla, se reintenta enviando al modelo
     su propio error para que lo corrija (hasta MAX_REINTENTOS veces).
"""
import logging
import re

import httpx  # se instala automáticamente junto con la librería ollama
import ollama
from pydantic import ValidationError

from config import MAX_REINTENTOS, MODELO, MODELO_VISION, NUM_CTX, OLLAMA_HOST, TIMEOUT_SEG
from schemas import PROMPT_SISTEMA, ResultadoDocumento

logger = logging.getLogger(__name__)

# Un único cliente reutilizable (mantiene la conexión HTTP abierta entre documentos).
_cliente = ollama.Client(host=OLLAMA_HOST, timeout=TIMEOUT_SEG)


class ErrorIA(Exception):
    """Fallo al clasificar un documento (afecta solo a ese documento)."""


class OllamaNoDisponible(ErrorIA):
    """Ollama no responde: no tiene sentido seguir procesando archivos."""


def verificar_ollama() -> None:
    """Comprueba al inicio que el servidor responde y que el modelo está descargado."""
    try:
        instalados = {m.model for m in _cliente.list().models}
    except ConnectionError as e:
        raise OllamaNoDisponible(
            f"No se pudo conectar con Ollama en {OLLAMA_HOST}. "
            "¿Está abierto? (debe aparecer el icono de la llama en la bandeja del sistema)."
        ) from e
    except ollama.ResponseError as e:
        raise ErrorIA(f"Ollama devolvió un error: {e.error}") from e

    # "llama3" y "llama3:latest" son el mismo modelo.
    if MODELO not in instalados and f"{MODELO}:latest" not in instalados:
        raise ErrorIA(f"El modelo '{MODELO}' no está descargado. Ejecuta:  ollama pull {MODELO}")


def clasificar_documento(texto: str) -> ResultadoDocumento:
    """Clasifica un documento a partir de su texto."""
    usuario = {"role": "user", "content": f'Texto del documento:\n"""\n{texto}\n"""'}
    return _clasificar(usuario, MODELO)


def clasificar_imagenes(imagenes: list[bytes]) -> ResultadoDocumento:
    """Clasifica un documento escaneado a partir de imágenes de sus primeras páginas."""
    usuario = {
        "role": "user",
        "content": "Estas son las primeras páginas de un documento escaneado. "
        "Léelas y clasifica el documento.",
        "images": imagenes,
    }
    return _clasificar(usuario, MODELO_VISION)


def _clasificar(mensaje_usuario: dict, modelo: str) -> ResultadoDocumento:
    """Núcleo común: llama al modelo, valida con Pydantic y reintenta si hace falta."""
    mensajes_base = [{"role": "system", "content": PROMPT_SISTEMA}, mensaje_usuario]
    mensajes = list(mensajes_base)
    esquema = ResultadoDocumento.model_json_schema()
    ultimo_error = "sin detalle"

    for intento in range(1, MAX_REINTENTOS + 1):
        contenido = _llamar_modelo(
            modelo,
            mensajes,
            esquema,
            # Primer intento determinista; en reintentos, algo de variación para no repetir el fallo.
            temperatura=0.0 if intento == 1 else 0.3,
        )

        try:
            # Valida JSON mal formado Y datos que no cumplen el esquema (misma excepción).
            return ResultadoDocumento.model_validate_json(_extraer_json(contenido))
        except ValidationError as e:
            ultimo_error = _resumir_error(e)
            logger.warning("   Intento %d/%d inválido: %s", intento, MAX_REINTENTOS, ultimo_error)
            # Retroalimentación: se muestra al modelo su respuesta y qué estuvo mal.
            mensajes = mensajes_base + [
                {"role": "assistant", "content": contenido},
                {
                    "role": "user",
                    "content": f"Tu respuesta no es válida ({ultimo_error}). "
                    "Devuelve de nuevo SOLO el JSON corregido.",
                },
            ]

    raise ErrorIA(f"El modelo no devolvió un JSON válido tras {MAX_REINTENTOS} intentos: {ultimo_error}")


# ---------------------------------------------------------------------------
# Auxiliares privadas
# ---------------------------------------------------------------------------
def _llamar_modelo(modelo: str, mensajes: list[dict], esquema: dict, temperatura: float) -> str:
    """Una llamada a Ollama; traduce los errores técnicos a mensajes claros."""
    try:
        respuesta = _cliente.chat(
            model=modelo,
            messages=mensajes,
            format=esquema,
            options={"temperature": temperatura, "num_ctx": NUM_CTX},
        )
    except ConnectionError as e:
        raise OllamaNoDisponible(f"Se perdió la conexión con Ollama en {OLLAMA_HOST}.") from e
    except httpx.TimeoutException as e:
        raise ErrorIA(f"Ollama tardó más de {TIMEOUT_SEG} s en responder.") from e
    except ollama.ResponseError as e:
        if e.status_code == 404:
            raise ErrorIA(f"Modelo '{modelo}' no encontrado. Ejecuta:  ollama pull {modelo}") from e
        raise ErrorIA(f"Ollama devolvió un error: {e.error}") from e

    return respuesta.message.content or ""


def _extraer_json(contenido: str) -> str:
    """Red de seguridad: quita ```json ... ``` o texto sobrante alrededor del objeto JSON."""
    contenido = re.sub(r"^```(?:json)?\s*|\s*```$", "", contenido.strip(), flags=re.IGNORECASE)
    inicio, fin = contenido.find("{"), contenido.rfind("}")
    if inicio != -1 and fin > inicio:
        return contenido[inicio : fin + 1]
    return contenido


def _resumir_error(error: ValidationError) -> str:
    """Convierte el error de Pydantic en una frase corta (sirve para el log y para el modelo)."""
    partes = []
    for e in error.errors():
        campo = ".".join(str(x) for x in e["loc"]) or "JSON"
        partes.append(f"{campo}: {e['msg']}")
    return "; ".join(partes)
