from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CorrespondenciaView, RecibidaView, EnviadaView, InternaView, generar_documento

# Create a router and register our viewset with it.
router = DefaultRouter()

# Registrar los viewsets con el router
router.register(r'correspondencia', CorrespondenciaView)
router.register(r'recibida', RecibidaView)
router.register(r'enviada', EnviadaView)
router.register(r'interna', InternaView)  

urlpatterns = [
    path('', include(router.urls)),
    path('generar-documento/<int:id>/', generar_documento, name='generar_documento'),
]