# Clasificador de documentos con IA local (Python + Ollama)

Script de automatización para Windows: lee PDF, DOCX y TXT de una carpeta, los clasifica con un
modelo de IA que corre **en tu propio equipo** (Ollama), renombra y organiza los archivos por
categoría, y genera un informe en Excel (y/o Word).

```
entrada/*.pdf|docx|txt -> extractor -> Ollama (JSON) -> Pydantic -> organizer -> salida/<Categoria>/ + informe
```

## Estructura

```
clasificador_documentos/
├── main.py            # Orquesta el flujo completo
├── config.py          # Rutas, modelo, límites y formato del informe
├── schemas.py         # Prompt de sistema + modelo Pydantic (validación)
├── extractor.py       # Texto desde PDF / DOCX / TXT
├── ia_client.py       # Conexión con Ollama + reintentos
├── organizer.py       # Mover/renombrar archivos + informe Excel/Word
├── requirements.txt
├── entrada/           # (se crea sola) deja aquí tus documentos
└── salida/            # (se crea sola) archivos organizados + informe
```

## Despliegue en Windows

1. **Instalar Ollama**: descarga el instalador desde https://ollama.com/download y ejecútalo.
   Queda como servicio en segundo plano (icono de la llama en la bandeja) escuchando en
   `http://localhost:11434`.
2. **Descargar el modelo** (PowerShell o CMD, ~4.7 GB la primera vez):
   ```
   ollama pull llama3:8b
   ollama run llama3:8b "Hola"      # prueba rápida; salir con /bye
   ```
   Alternativas: `ollama pull gemma2` (luego `set MODELO_OLLAMA=gemma2`) o `llama3.1:8b`.
3. **Python 3.10+**: comprueba con `py --version` (instálalo desde python.org marcando
   "Add Python to PATH" si hace falta).
4. **Entorno virtual e instalación de dependencias** (dentro de la carpeta del proyecto):
   ```
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   Si PowerShell bloquea el script de activación:
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, o usa CMD.
5. **Ejecutar**: copia tus documentos a `entrada\` y lanza
   ```
   python main.py
   ```
   El resultado queda en `salida\<Categoria>\` y en `salida\informe_clasificacion.xlsx`.

## Notas de uso

- Los archivos que fallan (PDF escaneado sin texto, JSON inválido tras 3 intentos...) **no se
  mueven**: quedan en `entrada\` y aparecen en el informe con el motivo en la columna *Estado*.
- Si el informe está abierto en Excel/Word, los resultados se guardan en un archivo con marca de
  tiempo para no perder nada. Cierra el informe antes de ejecutar para evitarlo.
- `config.py` permite cambiar modelo, copiar en vez de mover (`COPIAR_EN_VEZ_DE_MOVER = True`
  recomendado para tus primeras pruebas) y formato del informe (`"excel"`, `"word"`, `"ambos"`).
- **PDF escaneados o hechos de imágenes** (sin texto seleccionable): el script detecta que no hay
  texto y envía las primeras páginas como imagen a un modelo de visión. Una sola vez:
  ```
  python -m pip install pymupdf
  ollama pull gemma3:4b
  ```
  Es más lento que un PDF con texto (puede tardar 1-3 minutos por documento en un PC sin GPU).
  Solo se leen las primeras `PAGINAS_VISION` páginas (2 por defecto, en `config.py`).

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `No se pudo conectar con Ollama` | Ollama cerrado | Abre la app Ollama desde el menú Inicio |
| `El modelo ... no está descargado` | Falta el `pull` | `ollama pull llama3:8b` |
| `Modelo 'gemma3:4b' no encontrado` | Falta el modelo de visión | `ollama pull gemma3:4b` |
| `Falta PyMuPDF` | Falta la librería | `python -m pip install pymupdf` |
| `JSON inválido tras 3 intentos` | Modelo pequeño con texto confuso | Prueba `llama3.1:8b` o `gemma2` |
| Muy lento la primera vez | Ollama carga el modelo en RAM | Normal; los siguientes documentos son más rápidos |
