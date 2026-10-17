# Clasificador y Analizador de Documentos con IA Local (Gemma 2)

Script de automatización en Python que lee archivos PDF, DOCX y TXT, analiza su contenido con un modelo de IA local (Gemma 2 en Ollama), extrae información clave, renombra y clasifica los archivos por categoría, y genera un informe en Excel.

entrada/*.pdf|docx|txt -> extractor.py -> Ollama (gemma3:4b) -> organizer.py -> salida/<Categoria>/ + informe.xlsx
