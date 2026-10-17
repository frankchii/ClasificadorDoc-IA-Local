from datetime import datetime
from pathlib import Path
from config import CARPETA_ENTRADA, CARPETA_SALIDA
from extractor import extraer_contenido
from ia import clasificar_documento
from organizer import guardar_archivo, actualizar_informe

def main():
    CARPETA_ENTRADA.mkdir(exist_ok=True)
    CARPETA_SALIDA.mkdir(exist_ok=True)
    
    archivos = [
        p for p in CARPETA_ENTRADA.iterdir()
        if p.is_file() and p.suffix.lower() in [".pdf", ".docx", ".txt"]
    ]

    if not archivos:
        print("No se encontraron archivos en la carpeta 'entrada'.")
        return

    print(f"Archivos encontrados: {len(archivos)}\n")
    registros = []

    for i, archivo in enumerate(archivos, start=1):
        print(f"[{i}/{len(archivos)}] Procesando: {archivo.name}...")
        
        try:
            contenido = extraer_contenido(archivo)
            if contenido["tipo"] == "vacio":
                raise ValueError("El archivo está vacío.")
                
            datos = clasificar_documento(contenido)
            destino = guardar_archivo(archivo, datos)
            
            cat = datos.get("categoria", "Otro")
            res = datos.get("resumen", "-")
            clave = datos.get("datos_clave", "-")
            fecha = datos.get("fecha_documento", "desconocida")
            
            registros.append({
                "Fecha Proceso": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Archivo Original": archivo.name,
                "Archivo Nuevo": destino.name,
                "Categoría": cat,
                "Resumen": res,
                "Datos Clave": clave,
                "Fecha Documento": fecha,
                "Estado": "OK"
            })
            print(f"   -> Categoría: {cat} | Guardado como: {destino.name}")

        except Exception as e:
            print(f"   -> ERROR: {e}")
            registros.append({
                "Fecha Proceso": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Archivo Original": archivo.name,
                "Archivo Nuevo": "-",
                "Categoría": "-",
                "Resumen": "-",
                "Datos Clave": "-",
                "Fecha Documento": "-",
                "Estado": f"Error: {e}"
            })

    actualizar_informe(registros)
    print("\nProceso terminado. Informe guardado en 'salida/informe_clasificacion.xlsx'.")

if __name__ == "__main__":
    main()