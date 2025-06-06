from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CorrespondenciaView, DocEntranteView, DocSalienteView, DocInternoView, generar_documento

# Create a router and register our viewset with it.
router = DefaultRouter()

# Registrar los viewsets con el router
router.register(r'correspondencia', CorrespondenciaView)
router.register(r'correspondencia_entrante', DocEntranteView)
router.register(r'correspondencia_saliente', DocSalienteView)
router.register(r'correspondencia_interna', DocInternoView)  

urlpatterns = [
    path('', include(router.urls)),
    path('generar-documento/<int:id>/', generar_documento, name='generar_documento'),
]