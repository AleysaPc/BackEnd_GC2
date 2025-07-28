from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CorrespondenciaView, RecibidaView, EnviadaView, generar_documento, CorrespondenciaElaboradaView, AccionCorrespondenciaViewSet

# Create a router and register our viewset with it.
router = DefaultRouter()

# Registrar los viewsets con el router
router.register(r'correspondencia', CorrespondenciaView)
router.register(r'recibida', RecibidaView)
router.register(r'enviada', EnviadaView)
router.register(r'elaborada', CorrespondenciaElaboradaView)
router.register(r'acciones', AccionCorrespondenciaViewSet)
 

urlpatterns = [
    path('', include(router.urls)),
    path('generar-documento/<int:id>/', generar_documento, name='generar_documento'),
]