from django.db.models.signals import post_save
from django.dispatch import receiver
from documento.models import Documento
from documento.tasks import ocr_task

# En documento/signals.py:
@receiver(post_save, sender=Documento)
def procesar_documento_signal(sender, instance, created, **kwargs):
    if created and instance.archivo:
        # Pasar el ID en lugar de la ruta
        print(f"🚀 Disparando OCR para documento ID: {instance.id}")
        ocr_task.delay(instance.id)