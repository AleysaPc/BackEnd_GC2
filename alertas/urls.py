# alertas/urls.py
from django.urls import path
from . import views

app_name = 'alertas'

urlpatterns = [
    path('usuario/', views.alertas_usuario, name='alertas_usuario'),
    path('<int:alerta_id>/vista/', views.marcar_alerta_vista, name='marcar_alerta_vista'),
    path('crear/', views.crear_alerta_manual, name='crear_alerta_manual'),
]
from django.urls import path
from . import views

app_name = 'alertas'

urlpatterns = [
    path('usuario/', views.obtener_alertas_usuario, name='obtener_alertas_usuario'),
    path('estadisticas/', views.estadisticas_alertas, name='estadisticas_alertas'),
    path('<int:alerta_id>/vista/', views.marcar_alerta_vista, name='marcar_alerta_vista'),
    path('crear/', views.crear_alerta_manual, name='crear_alerta_manual'),
]