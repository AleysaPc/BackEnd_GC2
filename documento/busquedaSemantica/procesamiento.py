import os
from PIL import Image
from .ocr import extraer_texto_de_imagen, extraer_texto_de_pdf
from .clean_text import limpiar_texto_ocr
from .embeddings import generar_embedding
from documento.models import Documento

def procesar_documento(nombre_documento, ruta_archivo):
    ext = os.path.splitext(ruta_archivo)[1].lower()
    if ext in ['.png', '.jpg', '.jpeg']:
        imagen = Image.open(ruta_archivo)
        texto = extraer_texto_de_imagen(imagen)
    elif ext == '.pdf':
        texto = extraer_texto_de_pdf(ruta_archivo)
    else:
        print(f"Formato no soportado para OCR: {ext}")
        return

    texto_limpio = limpiar_texto_ocr(texto)
    embedding = generar_embedding(texto_limpio)

    try:
        doc = Documento.objects.filter(nombre_documento=nombre_documento).first()
        doc.contenido_extraido = texto_limpio
        if hasattr(embedding, 'tolist'):
            doc.vector_embedding = embedding.tolist()
        else:
            doc.vector_embedding = embedding
        doc.save(update_fields=['contenido_extraido', 'vector_embedding'])
        print(f"Documento '{nombre_documento}' procesado correctamente.")
    except Documento.DoesNotExist:
        print(f"Documento '{nombre_documento}' no encontrado en DB.")
