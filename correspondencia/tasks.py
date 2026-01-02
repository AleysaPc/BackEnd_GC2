from celery import shared_task

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def procesar_notificacion_task(self, recibida_id):
    from .models import Recibida
    from .signals_helper import procesar_notificacion

    instance = Recibida.objects.get(id_correspondencia=recibida_id)
    procesar_notificacion(instance)
