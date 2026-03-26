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
def ocr_task(self, documento_id):
    """Procesar OCR desde base64 storage"""
    import tempfile
    import os
    import time
    
    start_time = time.time()
    
    try:
        from documento.models import Documento
        doc = Documento.objects.get(id=documento_id)
        
        print(f"🔍 Procesando documento ID: {documento_id}")
        print(f"🔍 Nombre: {doc.nombre_documento}")
        
        # Obtener archivo temporal desde base64
        ruta_temporal = doc.get_archivo_temporal()
        
        if not ruta_temporal:
            raise ValueError("No se pudo crear archivo temporal desde base64")
        
        print(f"🔍 Archivo temporal: {ruta_temporal}")
        print(f"🔍 Existe archivo: {os.path.exists(ruta_temporal)}")
        
        # Procesar OCR con archivo temporal
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
        os.unlink(ruta_temporal)
        print(f"🧹 Archivo temporal eliminado: {ruta_temporal}")
        
        end_time = time.time()
        logger.info(f"[OCR] Documento '{doc.nombre_documento}' procesado en {end_time - start_time:.2f} seg")
        
        return {"nombre_documento": doc.nombre_documento, "texto": texto}
        
    except Documento.DoesNotExist:
        print(f"❌ Documento ID {documento_id} no encontrado")
        raise
    except Exception as e:
        print(f"❌ Error en OCR task: {str(e)}")
        raise
# -----------------------
# Task 2: Limpieza de texto
# -----------------------
@shared_task(bind=True)
def limpiar_task(self, ocr_result):
    """Limpiar texto extraído por OCR"""
    from documento.busquedaSemantica.clean_text import limpiar_texto_ocr
    
    texto_limpio = limpiar_texto_ocr(ocr_result['texto'])
    print(f"🧹 Texto limpiado: {len(texto_limpio)} caracteres")
    
    return {"texto_limpio": texto_limpio, "nombre_documento": ocr_result['nombre_documento']}

# -----------------------
# Task 3: Generación de embeddings
# -----------------------
@shared_task(bind=True)
def embeddings_task(self, limpiar_result):
    """Generar embeddings del texto limpio"""
    from documento.busquedaSemantica.embeddings import generar_embedding
    
    embedding = generar_embedding(limpiar_result['texto_limpio'])
    print(f"🔢 Embedding generado: {len(embedding)} dimensiones")
    
    return {"embedding": embedding, "texto_limpio": limpiar_result['texto_limpio'], "nombre_documento": limpiar_result['nombre_documento']}
 

# -----------------------
# Task 4: Guardar en BD
# -----------------------
@shared_task(bind=True)
def guardar_task(self, embeddings_result):
    """Guardar resultados en la base de datos"""
    from documento.models import Documento
    
    # Buscar por nombre_documento está bien, pero asegúrate que sea único
    doc = Documento.objects.get(nombre_documento=embeddings_result['nombre_documento'])
    doc.contenido_extraido = embeddings_result['texto_limpio']
    doc.vector_embedding = embeddings_result['embedding'].tolist() if hasattr(embeddings_result['embedding'], "tolist") else embeddings_result['embedding']
    doc.save(update_fields=["contenido_extraido", "vector_embedding"])
    
    print(f"💾 Documento guardado: {doc.nombre_documento}")
    return {"status": "completado", "documento": doc.nombre_documento}