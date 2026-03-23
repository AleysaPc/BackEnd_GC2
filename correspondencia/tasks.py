from celery import shared_task
from gestion_documental.ai.model_loader import get_model
#bind=True acceso a self
#autoretry_for reintenta si falla countdown=10 espera 10 segundos entre intentos
@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def procesar_notificacion_task(self, tipo, object_id):
    from .models import Recibida, CorrespondenciaElaborada
    from .signals_helper import (
        procesar_notificacion,
        procesar_notificacion_elaborada
    )

    if tipo == "recibida":
        instance = Recibida.objects.get(id_correspondencia=object_id)
        procesar_notificacion(instance)

    elif tipo == "elaborada":
        instance = CorrespondenciaElaborada.objects.get(id_correspondencia=object_id)
        procesar_notificacion_elaborada(instance)

    else:
        raise ValueError(f"Tipo de notificación no soportado: {tipo}")


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2, "countdown": 5})
def procesar_ia_pesada_task(self, texto):
    """
    Tarea de ejemplo para inferencia pesada.
    Mantiene la carga de sentence-transformers fuera del servicio web.
    """
    model = get_model()
    embedding = model.encode(texto).tolist()

    return {
        "ok": True,
        "dim": len(embedding),
        "preview": embedding[:5],
    }

#Define tareas Celery
#Maneja reintentos
#Llama la lógica pesada