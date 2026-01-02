from celery import shared_task 

#bind=True acceso a self
#autoretry_for reintenta si falla countdown=10 espera 10 segundos entre intentos
@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def procesar_notificacion_task(self, recibida_id): #solo se pasa el id
    from .models import Recibida
    from .signals_helper import procesar_notificacion

    instance = Recibida.objects.get(id_correspondencia=recibida_id) #Celery recupera el objeto ya confirmado en DB
    procesar_notificacion(instance)

#Define tareas Celery
#Maneja reintentos
#Llama la lógica pesada
