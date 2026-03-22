from django.db.models.signals import post_save
from django.dispatch import receiver
from documento.models import Documento
from documento.tasks import ocr_task

@receiver(post_save, sender=Documento)
def procesar_documento_signal(sender, instance, created, **kwargs):
    if created and instance.archivo:
        ocr_task.delay(instance.nombre_documento, instance.archivo.path)