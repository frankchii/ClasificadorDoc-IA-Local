from pathlib import Path
from docx import Document
import pymupdf

def extraer_contenido(ruta: Path) -> dict:
    ext = ruta.suffix.lower()
    
    if ext == ".txt":
        texto = ruta.read_text(encoding="utf-8", errors="ignore").strip()
        return {"tipo": "texto", "contenido": texto}
    
    elif ext == ".docx":
        doc = Document(str(ruta))
        lineas = [p.text for p in doc.paragraphs if p.text.strip()]
        for tabla in doc.tables:
            for fila in tabla.rows:
                lineas.append(" | ".join(c.text.strip() for c.text in fila.cells))
        texto = "\n".join(lineas).strip()
        return {"tipo": "texto", "contenido": texto}
    
    elif ext == ".pdf":
        doc = pymupdf.open(str(ruta))
        texto = []
        for page in doc[:10]:
            t = page.get_text()
            if t.strip():
                texto.append(t)
        
        texto_completo = "\n".join(texto).strip()
        
        if texto_completo:
            doc.close()
            return {"tipo": "texto", "contenido": texto_completo}
        
        if len(doc) > 0:
            pix = doc[0].get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            doc.close()
            return {"tipo": "imagen", "contenido": img_bytes}
            
        doc.close()
    
    return {"tipo": "vacio", "contenido": None}