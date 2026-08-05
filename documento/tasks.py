#Este archivo define las tareas individuales que ejecuta Celery. 

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
def ocr_task(self, id_documento, redis_key):
    """Procesar OCR desde Redis storage"""
    from documento.redis_utils import obtener_archivo_redis, limpiar_archivo_temporal
    
    print(f"🔍 Redis key recibida: {redis_key}")
    
    # Obtener archivo desde Redis
    ruta_temporal = obtener_archivo_redis(redis_key)
    
    if not ruta_temporal:
        raise ValueError(f"No se pudo obtener archivo desde Redis: {redis_key}")
    
    try:
        print(f"🔍 Archivo temporal: {ruta_temporal}")
        print(f"🔍 Existe archivo: {os.path.exists(ruta_temporal)}")
        
        # Procesar OCR
        ext = os.path.splitext(ruta_temporal)[1].lower()
        if ext in (".png", ".jpg", ".jpeg"):
            from PIL import Image
            imagen = Image.open(ruta_temporal)
            texto = extraer_texto_de_imagen(imagen)
        elif ext == ".pdf":
            texto = extraer_texto_de_pdf(ruta_temporal)
        else:
            raise ValueError(f"Formato no soportado: {ext}")
        
        # Limpiar archivo temporal
        limpiar_archivo_temporal(ruta_temporal)
        
        return {"id_documento": id_documento, "texto": texto}
        
    except Exception as e:
        limpiar_archivo_temporal(ruta_temporal)
        raise
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
def embeddings_task(self, data, chunk_size=256): #Chunk fragmento o trozo de texto. 
    start_time = time.time()
    texto = data["texto_limpio"]
    # Dividir en chunks si es muy largo
    #chunks = [texto[i:i+chunk_size] for i in range(0, len(texto), chunk_size)]
    #embeddings = [generar_embedding(chunk).tolist() for chunk in chunks]
    embeddings = generar_embedding(texto).tolist()
    data["embeddings"] = embeddings
    end_time = time.time()
    #logger.info(f"[Embeddings] Documento '{data['nombre_documento']}' embeddings generados en {end_time - start_time:.2f} seg")
    return data

    embedding = generar_embedding(texto)

    print("Tipo embedding:", type(embedding))
    print("Shape:", embedding.shape)

    data["embeddings"] = embedding.tolist()


    import numpy as np

    emb = np.asarray(data["embeddings"])

    print("Shape antes de guardar:", emb.shape)

# -----------------------
# Task 4: Guardar en BD
# -----------------------
@shared_task(bind=True)
def guardar_task(self, data):
    start_time = time.time()

    id_documento = data["id_documento"]
    doc = Documento.objects.get(pk=id_documento)

    # ===== DEPURACIÓN =====
    emb = data["embeddings"]

    print("Tipo de emb:", type(emb))
    print("Longitud:", len(emb))
    print("Tipo del primer elemento:", type(emb[0]))
    print("Primeros 5 valores:", emb[:5])

    # ======================

    doc.contenido_extraido = data["texto_limpio"]
    doc.vector_embedding = emb

    doc.save(update_fields=["contenido_extraido", "vector_embedding"])

    end_time = time.time()
    logger.info(f"[BD] Documento '{id_documento}' guardado en {end_time - start_time:.2f} seg")

    return doc.pk