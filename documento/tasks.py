from celery import shared_task
from celery.utils.log import get_task_logger
from documento.busquedaSemantica.ocr import extraer_texto_de_pdf, extraer_texto_de_imagen
from documento.busquedaSemantica.clean_text import limpiar_texto_ocr
from documento.busquedaSemantica.embeddings import generar_embedding
from documento.models import Documento
from PIL import Image
import os
import time

# -----------------------
# Logger
# -----------------------
logger = get_task_logger(__name__)

# -----------------------
# Task 1: OCR
# -----------------------
@shared_task(bind=True)
def ocr_task(self, nombre_documento, ruta_archivo):
    start_time = time.time()
    ext = os.path.splitext(ruta_archivo)[1].lower()

    if ext in (".png", ".jpg", ".jpeg"):
        imagen = Image.open(ruta_archivo)
        texto = extraer_texto_de_imagen(imagen)
    elif ext == ".pdf":
        texto = extraer_texto_de_pdf(ruta_archivo)
    else:
        raise ValueError(f"Formato no soportado: {ext}")

    end_time = time.time()
    logger.info(f"[OCR] Documento '{nombre_documento}' procesado en {end_time - start_time:.2f} seg")
    return {"nombre_documento": nombre_documento, "texto": texto}

# -----------------------
# Task 2: Limpieza de texto
# -----------------------
@shared_task(bind=True)
def limpiar_task(self, data):
    start_time = time.time()
    texto_limpio = limpiar_texto_ocr(data["texto"])
    data["texto_limpio"] = texto_limpio
    end_time = time.time()
    #logger.info(f"[Limpieza] Documento '{data['nombre_documento']}' limpio en {end_time - start_time:.2f} seg")
    return data

# -----------------------
# Task 3: Generación de embeddings
# -----------------------
@shared_task(bind=True)
def embeddings_task(self, data, chunk_size=1000):
    start_time = time.time()
    texto = data["texto_limpio"]
    # Dividir en chunks si es muy largo
    chunks = [texto[i:i+chunk_size] for i in range(0, len(texto), chunk_size)]
    embeddings = [generar_embedding(chunk).tolist() for chunk in chunks]
    data["embeddings"] = embeddings
    end_time = time.time()
    #logger.info(f"[Embeddings] Documento '{data['nombre_documento']}' embeddings generados en {end_time - start_time:.2f} seg")
    return data

# -----------------------
# Task 4: Guardar en BD
# -----------------------
@shared_task(bind=True)
def guardar_task(self, data):
    start_time = time.time()
    nombre_documento = data["nombre_documento"]
    doc = Documento.objects.filter(nombre_documento=nombre_documento).first()
    if not doc:
        raise ValueError(f"Documento '{nombre_documento}' no encontrado en BD")

    # Promediar todos los embeddings
    import numpy as np
    embeddings = np.array(data["embeddings"])
    embedding_promedio = np.mean(embeddings, axis=0).tolist()
    
    doc.contenido_extraido = data["texto_limpio"]
    doc.vector_embedding = embedding_promedio
    doc.save(update_fields=["contenido_extraido", "vector_embedding"])
    
    end_time = time.time()
    logger.info(f"[BD] Documento '{nombre_documento}' guardado en {end_time - start_time:.2f} seg")
    return doc.pk
