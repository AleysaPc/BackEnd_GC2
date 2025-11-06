from .views import DocumentoViewSet, PlantillaDocumentoViewSet, buscar_documentos_semanticos
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Crear un router y registrar los viewsets
router = DefaultRouter()

# Registrar los viewsets con el router
router.register(r'documento', DocumentoViewSet)
router.register(r'plantillaDocumento', PlantillaDocumentoViewSet)


# urlpatterns para incluir las rutas del router
urlpatterns = [
    path('', include(router.urls)),
    path('buscar_documentos_semanticos/', buscar_documentos_semanticos),
]