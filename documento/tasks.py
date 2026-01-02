from celery import shared_task
from documento.busquedaSemantica.procesamiento import procesar_documento

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def procesar_documento_task(self, nombre_documento, ruta_archivo):
    """
    Tarea Celery para OCR MÁS EMBEDDINGS
    """
    procesar_documento(nombre_documento,ruta_archivo)