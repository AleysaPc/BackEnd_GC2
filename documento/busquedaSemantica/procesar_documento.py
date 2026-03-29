#Este archivo es como un orquestador, asegura que las tareas se ejecuten en orden correcto. 
import os
from celery import chain
from documento.tasks import ocr_task, limpiar_task, embeddings_task, guardar_task

def procesar_documento(nombre_documento: str, redis_key: str, async_processing: bool = True) -> None:
    """
    Procesa un documento de forma síncrona o asíincrona usando Celery
    
    Args:
        nombre_documento: Nombre del documento a procesar
        redis_key: Clave en Redis donde está el archivo
    """
    if async_processing:
        # Versión asíncrona usando Celery
        chain(
            ocr_task.s(nombre_documento, redis_key),  # ← Cambiar aquí
            limpiar_task.s(),
            embeddings_task.s(),
            guardar_task.s()
        ).apply_async()
    # Reemplaza todo el bloque else:
    else:
        # Versión síncrona usando Redis
        from documento.models import Documento
        from documento.redis_utils import obtener_archivo_redis, limpiar_archivo_temporal
        from documento.busquedaSemantica.ocr import extraer_texto_de_imagen, extraer_texto_de_pdf
        from documento.busquedaSemantica.clean_text import limpiar_texto_ocr
        from documento.busquedaSemantica.embeddings import generar_embedding
        from PIL import Image
        
        doc = Documento.objects.get(nombre_documento=nombre_documento)
        ruta_temporal = obtener_archivo_redis(redis_key)
        
        if not ruta_temporal:
            raise ValueError("No se pudo crear archivo temporal desde Redis")
        
        try:
            # 1️⃣ OCR
            ext = os.path.splitext(ruta_temporal)[1].lower()
            if ext in (".png", ".jpg", ".jpeg"):
                imagen = Image.open(ruta_temporal)
                texto = extraer_texto_de_imagen(imagen)
            elif ext == ".pdf":
                texto = extraer_texto_de_pdf(ruta_temporal)
            else:
                raise ValueError(f"Formato no soportado: {ext}")

            # 2️⃣ Limpieza
            texto_limpio = limpiar_texto_ocr(texto)
            
            # 3️⃣ Generar embeddings
            embedding = generar_embedding(texto_limpio)
            
            # 4️⃣ Guardar en BD
            doc.contenido_extraido = texto_limpio
            doc.vector_embedding = embedding.tolist() if hasattr(embedding, "tolist") else embedding
            doc.save(update_fields=["contenido_extraido", "vector_embedding"])
            
        finally:
            limpiar_archivo_temporal(ruta_temporal)