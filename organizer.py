import shutil
from pathlib import Path
import pandas as pd
from config import CARPETA_SALIDA, COPIAR_ARCHIVOS

INFORME_PATH = CARPETA_SALIDA / "informe_clasificacion.xlsx"

def guardar_archivo(origen: Path, datos: dict) -> Path:
    categoria = datos.get("categoria", "Otro")
    nuevo_nombre = datos.get("nuevo_nombre", origen.stem)
    
    destino_dir = CARPETA_SALIDA / categoria
    destino_dir.mkdir(parents=True, exist_ok=True)
    
    destino_path = destino_dir / f"{nuevo_nombre}{origen.suffix.lower()}"
    
    contador = 1
    while destino_path.exists():
        destino_path = destino_dir / f"{nuevo_nombre}_{contador}{origen.suffix.lower()}"
        contador += 1

    if COPIAR_ARCHIVOS:
        shutil.copy2(origen, destino_path)
    else:
        shutil.move(str(origen), destino_path)
        
    return destino_path

def actualizar_informe(registros: list[dict]):
    if not registros:
        return

    df_nuevo = pd.DataFrame(registros)
    
    if INFORME_PATH.exists():
        df_existente = pd.read_excel(INFORME_PATH)
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    else:
        df_final = df_nuevo

    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    df_final.to_excel(INFORME_PATH, index=False)