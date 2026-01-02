import os
from PIL import Image
from .ocr import extraer_texto_de_imagen, extraer_texto_de_pdf
from .clean_text import limpiar_texto_ocr
from .embeddings import generar_embedding
from documento.models import Documento

def procesar_documento(nombre_documento, ruta_archivo):
    #Detección del tipo de archivo
    ext = os.path.splitext(ruta_archivo)[1].lower()
    if ext in ['.png', '.jpg', '.jpeg']:
        imagen = Image.open(ruta_archivo)
        texto = extraer_texto_de_imagen(imagen)
    elif ext == '.pdf':
        texto = extraer_texto_de_pdf(ruta_archivo)
    else:
        print(f"Formato no soportado para OCR: {ext}")
        return
    #Limpieza del texto 
    texto_limpio = limpiar_texto_ocr(texto)
    #Generación de embeddings
    embedding = generar_embedding(texto_limpio)

    #Busca en la BD un documento con ese nombre
    doc = Documento.objects.filter(nombre_documento=nombre_documento).first()

    #Si el documento no fue encontrado. 
    if not doc:
        print(f"Documento '{nombre_documento}' no encontrado en DB.")
        return
    #Guarda el texto OCR limpio en el modelo Documento
    doc.contenido_extraido = texto_limpio

    if hasattr(embedding, 'tolist'):
        #Convierte el vector a lista Python para poder guardar en JSONField, ArrayField, VectorField
        doc.vector_embedding = embedding.tolist()
    else:
        doc.vector_embedding = embedding
            #Solo actualiza campos
    doc.save(update_fields=['contenido_extraido', 'vector_embedding'])
