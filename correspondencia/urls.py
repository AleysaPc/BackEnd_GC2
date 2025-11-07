from ntpath import basename
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CorrespondenciaView, RecibidaView, EnviadaView, CorrespondenciaElaboradaView, AccionCorrespondenciaViewSet, generar_documento, notificaciones_pendientes, marcar_notificacion_vista
# Create a router and register our viewset with it.
router = DefaultRouter()


# ===========================
# RUTAS DE VIEWSETS
# ===========================
router.register(r'correspondencia', CorrespondenciaView)
router.register(r'recibida', RecibidaView)
router.register(r'enviada', EnviadaView)
router.register(r'elaborada', CorrespondenciaElaboradaView)
router.register(r'acciones', AccionCorrespondenciaViewSet, basename='acciones')
 
# ===========================
# RUTAS PERSONALIZADAS
# ===========================
urlpatterns = [
    path('', include(router.urls)),
    #Generación de documentos
    path('generar_documento/<int:doc_id>/', generar_documento, name='generar_documento'),
    #Notificaciones
    path('notificacion/pendiente/', notificaciones_pendientes, name='notificaciones_pendientes'),
    path('notificacion/vista/<int:id_accion>/', marcar_notificacion_vista, name='marcar_notificacion_vista'),
]