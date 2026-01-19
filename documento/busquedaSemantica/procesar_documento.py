import os
from celery import chain
from documento.tasks import ocr_task, limpiar_task, embeddings_task, guardar_task

def procesar_documento(nombre_documento: str, ruta_archivo: str, async_processing: bool = True) -> None:
    """
    Procesa un documento de forma síncrona o asíncrona usando Celery.
    
    Args:
        nombre_documento: Nombre del documento a procesar
        ruta_archivo: Ruta completa al archivo a procesar
        async_processing: Si es True, usa Celery para procesamiento asíncrono
    """
    if async_processing:
        # Versión asíncrona usando Celery
        chain(
            ocr_task.s(nombre_documento, ruta_archivo),
            limpiar_task.s(),
            embeddings_task.s(),
            guardar_task.s()
        ).apply_async()
    else:
        # Versión síncrona (solo para pruebas o casos especiales)
        from documento.models import Documento
        from documento.busquedaSemantica.ocr import extraer_texto_de_imagen, extraer_texto_de_pdf
        from documento.busquedaSemantica.clean_text import limpiar_texto_ocr
        from documento.busquedaSemantica.embeddings import generar_embedding
        from PIL import Image
        
        # 1️⃣ OCR
        ext = os.path.splitext(ruta_archivo)[1].lower()
        if ext in (".png", ".jpg", ".jpeg"):
            imagen = Image.open(ruta_archivo)
            texto = extraer_texto_de_imagen(imagen)
        elif ext == ".pdf":
            texto = extraer_texto_de_pdf(ruta_archivo)
        else:
            raise ValueError(f"Formato no soportado: {ext}")

        # 2️⃣ Limpieza
        texto_limpio = limpiar_texto_ocr(texto)
        
        # 3️⃣ Generar embeddings (versión simple sin chunks)
        embedding = generar_embedding(texto_limpio)
        
        # 4️⃣ Guardar en BD
        doc = Documento.objects.filter(nombre_documento=nombre_documento).first()
        if not doc:
            raise ValueError(f"Documento '{nombre_documento}' no encontrado en BD")
            
        doc.contenido_extraido = texto_limpio
        doc.vector_embedding = embedding.tolist() if hasattr(embedding, "tolist") else embedding
        doc.save(update_fields=["contenido_extraido", "vector_embedding"])