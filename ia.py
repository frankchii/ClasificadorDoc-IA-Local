import json
import ollama
from config import MODELO_OLLAMA

PROMPT = """Eres un asistente que clasifica y analiza documentos de cualquier tipo.
Responde UNICAMENTE con un objeto JSON con esta estructura exacta:

{
  "categoria": "Factura | Contrato | Informe | Carta | Resolucion | Catalogo | Academico | Curriculum | Otro",
  "resumen": "Explicacion de 2 a 3 oraciones completas sobre el tema principal, el objetivo y las partes o datos clave del documento.",
  "datos_clave": "Extrae de 3 a 5 datos clave en formato 'Clave: Valor | Clave: Valor' (ejemplo: 'Monto: 1500 | Vencimiento: 2026-11-01' o 'Candidato: Juan | Carrera: Ingenieria')",
  "fecha_documento": "AAAA-MM-DD o 'desconocida'",
  "nuevo_nombre": "Categoria_Tema_AAAA-MM-DD"
}

Reglas:
1. El nuevo_nombre no debe llevar espacios ni tildes, usa guiones bajos (_).
2. Si no hay fecha, pon 'desconocida'.
3. Responde solo el JSON sin texto extra.
"""

def clasificar_documento(contenido: dict) -> dict:
    tipo = contenido["tipo"]
    
    if tipo == "texto":
        mensaje = {"role": "user", "content": f"Texto del documento:\n{contenido['contenido'][:6000]}"}
    elif tipo == "imagen":
        mensaje = {
            "role": "user",
            "content": "Este es un documento escaneado. Lee el contenido visualmente y clasifícalo.",
            "images": [contenido["contenido"]]
        }
    else:
        raise ValueError("El archivo no contiene texto ni imágenes procesables.")

    respuesta = ollama.chat(
        model=MODELO_OLLAMA,
        messages=[
            {"role": "system", "content": PROMPT},
            mensaje
        ],
        format="json"
    )
    
    datos = json.loads(respuesta.message.content)
    
    if "nuevo_nombre" in datos:
        nombre = datos["nuevo_nombre"]
        for c in [" ", "/", "\\", ":", "*", "?", '"', "<", ">", "|"]:
            nombre = nombre.replace(c, "_")
        datos["nuevo_nombre"] = nombre
        
    return datos