# SystemGC2/Backend/gestion_documental/celery.py
import os
from celery import Celery

# Define settings del proyecto principal
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_documental.settings')

app = Celery('gestion_documental')

# Cargar configuración de Django con prefijo CELERY_*
app.config_from_object('django.conf:settings', namespace='CELERY')

# Buscar tasks.py automáticamente en apps
app.autodiscover_tasks()
