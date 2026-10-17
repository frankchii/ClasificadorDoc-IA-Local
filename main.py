"""
main.py - Orquestador del flujo completo.

    entrada/*.pdf|docx|txt  ->  extraer texto  ->  Ollama (JSON)  ->  validar (Pydantic)
                            ->  renombrar y mover a salida/<Categoria>/  ->  informe Excel/Word

Uso (desde la carpeta del proyecto):
    python main.py
"""
import logging
import sys
import time
from pathlib import Path

from config import CARPETA_ENTRADA, CARPETA_SALIDA, EXTENSIONES_SOPORTADAS, MODELO, MODELO_VISION
from extractor import ExtraccionError, SinTextoError, extraer_texto, renderizar_paginas_pdf
from ia_client import (
    ErrorIA,
    OllamaNoDisponible,
    clasificar_documento,
    clasificar_imagenes,
    verificar_ollama,
)
from organizer import actualizar_informe, organizar_archivo, registro_error, registro_ok

logger = logging.getLogger("main")


def listar_archivos() -> list[Path]:
    """Archivos soportados de la carpeta de entrada (ignora temporales '~$' que crea Word)."""
    return sorted(
        p
        for p in CARPETA_ENTRADA.iterdir()
        if p.is_file()
        and p.suffix.lower() in EXTENSIONES_SOPORTADAS
        and not p.name.startswith("~$")
    )


def clasificar_archivo(ruta: Path):
    """Texto -> modelo de texto. Si es un PDF sin texto (escaneo) -> modelo de visión."""
    try:
        return clasificar_documento(extraer_texto(ruta))
    except SinTextoError:
        logger.info("   PDF sin texto: se analizan las primeras páginas como imagen (%s)", MODELO_VISION)
        return clasificar_imagenes(renderizar_paginas_pdf(ruta))


def procesar_archivo(ruta: Path) -> dict:
    """Procesa UN archivo y devuelve la fila del informe (OK o ERROR).

    Un fallo en un documento no detiene el lote: se registra y se sigue con el siguiente.
    Solo OllamaNoDisponible se propaga, porque sin servidor no tiene sentido continuar.
    """
    try:
        resultado = clasificar_archivo(ruta)              # 1-2. leer + IA + validación Pydantic
        destino = organizar_archivo(ruta, resultado)      # 3. renombrar y mover
        logger.info("   -> %s / %s", resultado.categoria, destino.name)
        return registro_ok(ruta, destino, resultado)
    except OllamaNoDisponible:
        raise
    except (ExtraccionError, ErrorIA, OSError) as e:
        logger.error("   -> ERROR: %s", e)
        return registro_error(ruta, str(e))


def main() -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S"
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)  # oculta el ruido de cada petición HTTP
    CARPETA_ENTRADA.mkdir(exist_ok=True)
    CARPETA_SALIDA.mkdir(exist_ok=True)

    archivos = listar_archivos()
    if not archivos:
        logger.warning("No hay archivos PDF/DOCX/TXT en: %s", CARPETA_ENTRADA)
        return 0

    try:
        verificar_ollama()  # falla rápido, antes de procesar nada
    except ErrorIA as e:
        logger.error("%s", e)
        return 1

    logger.info("Modelo: %s | Archivos a procesar: %d", MODELO, len(archivos))
    inicio = time.perf_counter()
    registros: list[dict] = []

    try:
        for i, ruta in enumerate(archivos, start=1):
            logger.info("[%d/%d] %s", i, len(archivos), ruta.name)
            registros.append(procesar_archivo(ruta))
    except OllamaNoDisponible as e:
        logger.error("%s Se detiene el proceso.", e)
    except KeyboardInterrupt:
        logger.warning("Interrumpido por el usuario (Ctrl+C).")
    finally:
        # Pase lo que pase, lo ya procesado queda guardado en el informe.
        if registros:
            rutas = actualizar_informe(registros)
            correctos = sum(1 for r in registros if r["Estado"] == "OK")
            logger.info(
                "Terminado en %.1f s: %d correctos, %d con error.",
                time.perf_counter() - inicio, correctos, len(registros) - correctos,
            )
            for ruta_informe in rutas:
                logger.info("Informe: %s", ruta_informe)

    return 0


if __name__ == "__main__":
    sys.exit(main())
