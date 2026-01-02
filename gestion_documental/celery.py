
import os
from celery import Celery #Importación de celery

#Arranque de Celery

# Define settings del proyecto principal - “Usa los settings de Django como si fueras Django”
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_documental.settings')

# app equivale a Django --> settings.py Celery-->app
app = Celery('gestion_documental')

# Cargar configuración de Django con prefijo CELERY_*
# “Busca tu configuración dentro de settings.py usando el prefijo CELERY_”
app.config_from_object('django.conf:settings', namespace='CELERY')

# Buscar tasks.py automáticamente en apps
app.autodiscover_tasks()

#Inicializa Celery
#Conecta Celery con Django
#Carga configuración
#Descubre tareas automáticamente