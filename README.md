# Clasificador y Analizador de Documentos con IA Local

Script de automatización en Python que analiza, clasifica y organiza documentos (PDF, DOCX y TXT) de forma 100% local utilizando Ollama y Gemma 3. Genera un reporte estructurado en Excel con resúmenes y datos clave extraídos de cada archivo.

---

## Flujo de Trabajo

`entrada/` (PDF, DOCX, TXT) ➔ `extractor.py` (Texto / Visión OCR) ➔ `ia.py` (Ollama + Gemma 3) ➔ `organizer.py` ➔ `salida/<Categoria>/` + `informe_clasificacion.xlsx`

---

## Características Principales

* **Soporte Híbrido (Texto + OCR):** Lee texto digital de PDFs, DOCX y TXT. Si el PDF es un documento escaneado (imagen), utiliza la capacidad de visión de Gemma 3 para procesarlo visualmente.
* **100% Local y Privado:** Toda la inferencia corre en tu propia máquina mediante Ollama. Ningún dato sale a la nube.
* **Análisis Estructurado:** Genera resúmenes explicativos de 2 a 3 oraciones, detecta la fecha del documento y extrae pares clave-valor (montos, emisor, candidato, etc.).
* **Organización Segura:** Renombra los archivos sin espacios ni caracteres especiales de Windows y maneja colisiones numéricas (`_1`, `_2`) para evitar sobreescrituras accidentales.
* **Reporte Consolidado:** Acumula automáticamente todo el historial de procesamiento en un archivo Excel (`salida/informe_clasificacion.xlsx`).

---

## Estructura del Proyecto

* **`main.py`**: Coordinador general del flujo.
* **`config.py`**: Configuración centralizada de rutas y modelo de IA.
* **`extractor.py`**: Extracción de texto y renderizado de imágenes para PDFs escaneados usando PyMuPDF.
* **`ia.py`**: Conexión con Ollama para análisis y generación de respuestas JSON.
* **`organizer.py`**: Creación de subcarpetas, movimiento de archivos y actualización del informe Excel.
* **`requirements.txt`**: Librerías de Python requeridas.
* **`entrada/`**: Carpeta de origen donde se depositan los documentos sin clasificar.
* **`salida/`**: Carpeta de destino con archivos organizados por categoría y el reporte consolidado.

---

## Requisitos Previos

1. **Python 3.10+**
2. **Ollama** instalado y ejecutándose en segundo plano ([Descargar Ollama](https://ollama.com/download))
3. Modelo **Gemma 3** descargado en Ollama:
   ```bash
   ollama pull gemma3:4b
