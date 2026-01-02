#Para que Celery se cargue automáticamente:
from .celery import app as celery_app

__all__ = ['celery_app']
