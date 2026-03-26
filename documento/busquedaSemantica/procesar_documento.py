#Este archivo es como un orquestador, asegura que las tareas se ejecuten en orden correcto. 
import os
from celery import chain
from documento.tasks import ocr_task, limpiar_task, embeddings_task, guardar_task

def procesar_documento(documento_id: int, async_processing: bool = True) -> None:
    """
    Procesa un documento usando base64 storage.
    
    Args:
        documento_id: ID del documento a procesar
        async_processing: Si es True, usa Celery para procesamiento asíncrono
    """
    if async_processing:
        # Versión asíncrona usando Celery
        chain(
            ocr_task.s(documento_id),  # Solo pasar documento_id
            limpiar_task.s(),
            embeddings_task.s(),
            guardar_task.s()
        ).apply_async()
    else:
        # Versión síncrona
        from documento.models import Documento
        doc = Documento.objects.get(id=documento_id)
        
        # Obtener archivo temporal desde base64
        ruta_temporal = doc.get_archivo_temporal()
        
        if not ruta_temporal:
            raise ValueError("No se pudo crear archivo temporal desde base64")
        
        # Procesar OCR síncrono
        from documento.busquedaSemantica.ocr import extraer_texto_de_imagen, extraer_texto_de_pdf
        from documento.busquedaSemantica.clean_text import limpiar_texto_ocr
        from documento.busquedaSemantica.embeddings import generar_embedding
        from PIL import Image
        import os
        
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
        
        # Limpiar archivo temporal
        os.unlink(ruta_temporal)