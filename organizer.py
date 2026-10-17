"""
organizer.py - Organiza los archivos en subcarpetas y genera/actualiza el informe.

Responsabilidades:
  - organizar_archivo(): renombra y mueve (o copia) cada archivo a salida/<Categoria>/.
  - registro_ok() / registro_error(): construyen una fila del informe.
  - actualizar_informe(): añade las filas nuevas al informe Excel y/o Word.
"""
import logging
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.shared import Pt
from openpyxl.utils import get_column_letter

from config import (
    CARPETA_SALIDA,
    COPIAR_EN_VEZ_DE_MOVER,
    FORMATO_INFORME,
    NOMBRE_INFORME,
)
from schemas import ResultadoDocumento

logger = logging.getLogger(__name__)

COLUMNAS_INFORME = [
    "Fecha de proceso",
    "Archivo original",
    "Archivo nuevo",
    "Categoría",
    "Resumen",
    "Fecha del documento",
    "Estado",
]
ANCHOS_EXCEL = {"Archivo original": 32, "Archivo nuevo": 38, "Resumen": 70, "Fecha de proceso": 20}


# ---------------------------------------------------------------------------
# 1. Organización de archivos
# ---------------------------------------------------------------------------
def organizar_archivo(origen: Path, resultado: ResultadoDocumento) -> Path:
    """Mueve/copia el archivo a salida/<Categoria>/<nuevo_nombre><ext> y devuelve la ruta final."""
    carpeta_destino = CARPETA_SALIDA / resultado.categoria
    carpeta_destino.mkdir(parents=True, exist_ok=True)

    nombre_final = f"{resultado.nuevo_nombre}{origen.suffix.lower()}"
    destino = _ruta_sin_colision(carpeta_destino / nombre_final)

    if COPIAR_EN_VEZ_DE_MOVER:
        shutil.copy2(origen, destino)
    else:
        shutil.move(str(origen), str(destino))
    return destino


def _ruta_sin_colision(ruta: Path) -> Path:
    """Si ya existe un archivo con ese nombre, añade _2, _3... para no sobrescribirlo."""
    if not ruta.exists():
        return ruta
    contador = 2
    while True:
        candidata = ruta.with_name(f"{ruta.stem}_{contador}{ruta.suffix}")
        if not candidata.exists():
            return candidata
        contador += 1


# ---------------------------------------------------------------------------
# 2. Filas del informe
# ---------------------------------------------------------------------------
def registro_ok(origen: Path, destino: Path, r: ResultadoDocumento) -> dict:
    return {
        "Fecha de proceso": _ahora(),
        "Archivo original": origen.name,
        "Archivo nuevo": destino.name,
        "Categoría": r.categoria,
        "Resumen": _texto_seguro_excel(r.resumen),
        "Fecha del documento": r.fecha_documento,
        "Estado": "OK",
    }


def registro_error(origen: Path, motivo: str) -> dict:
    return {
        "Fecha de proceso": _ahora(),
        "Archivo original": origen.name,
        "Archivo nuevo": "-",
        "Categoría": "-",
        "Resumen": "-",
        "Fecha del documento": "-",
        "Estado": f"ERROR: {motivo[:200]}",
    }


def _ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _texto_seguro_excel(texto: str) -> str:
    """Evita 'inyección de fórmulas': un texto que empiece con = + - @ se interpretaría como fórmula."""
    return "'" + texto if texto[:1] in ("=", "+", "-", "@") else texto


# ---------------------------------------------------------------------------
# 3. Informe (Excel y/o Word)
# ---------------------------------------------------------------------------
def actualizar_informe(registros: list[dict]) -> list[Path]:
    """Añade los registros al informe (lo crea si no existe). Devuelve las rutas escritas."""
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    df_nuevo = pd.DataFrame(registros, columns=COLUMNAS_INFORME)

    excel, word = (_guardar_excel, ".xlsx"), (_guardar_word, ".docx")
    escritores = {"excel": [excel], "word": [word], "ambos": [excel, word]}
    if FORMATO_INFORME not in escritores:
        raise ValueError(f"FORMATO_INFORME inválido: '{FORMATO_INFORME}' (usa excel, word o ambos)")

    rutas = []
    for guardar, extension in escritores[FORMATO_INFORME]:
        ruta = CARPETA_SALIDA / f"{NOMBRE_INFORME}{extension}"
        try:
            guardar(df_nuevo, ruta)
        except PermissionError:
            # En Windows, si el archivo está abierto en Excel/Word no se puede escribir.
            # No perdemos los resultados: se guardan en un archivo alternativo con marca de tiempo.
            marca = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta = ruta.with_name(f"{ruta.stem}_{marca}{ruta.suffix}")
            logger.warning("El informe está abierto en otro programa. Se guardará en: %s", ruta.name)
            guardar(df_nuevo, ruta)
        rutas.append(ruta)
    return rutas


def _guardar_excel(df_nuevo: pd.DataFrame, ruta: Path) -> None:
    """Si el .xlsx existe, conserva sus filas anteriores y añade las nuevas al final."""
    df = pd.concat([pd.read_excel(ruta), df_nuevo], ignore_index=True) if ruta.exists() else df_nuevo

    with pd.ExcelWriter(ruta, engine="openpyxl") as escritor:
        df.to_excel(escritor, sheet_name="Informe", index=False)
        hoja = escritor.sheets["Informe"]
        for i, columna in enumerate(df.columns, start=1):
            hoja.column_dimensions[get_column_letter(i)].width = ANCHOS_EXCEL.get(columna, 18)
        hoja.freeze_panes = "A2"  # encabezado siempre visible


def _guardar_word(df_nuevo: pd.DataFrame, ruta: Path) -> None:
    """Si el .docx existe, añade filas a su tabla; si no, crea el documento con encabezado."""
    if ruta.exists():
        documento = Document(str(ruta))
        tabla = documento.tables[0]
    else:
        documento = Document()
        documento.styles["Normal"].font.size = Pt(9)
        seccion = documento.sections[0]  # horizontal: la tabla tiene 7 columnas
        seccion.orientation = WD_ORIENT.LANDSCAPE
        seccion.page_width, seccion.page_height = seccion.page_height, seccion.page_width

        documento.add_heading("Informe de clasificación de documentos", level=1)
        tabla = documento.add_table(rows=1, cols=len(COLUMNAS_INFORME))
        tabla.style = "Table Grid"
        for celda, titulo in zip(tabla.rows[0].cells, COLUMNAS_INFORME):
            celda.text = ""
            celda.paragraphs[0].add_run(titulo).bold = True

    for fila in df_nuevo.itertuples(index=False):
        for celda, valor in zip(tabla.add_row().cells, fila):
            celda.text = str(valor)

    documento.save(str(ruta))
