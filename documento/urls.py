from .views import TipoDocumentoViewSet, DocumentoViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Crear un router y registrar los viewsets
router = DefaultRouter()

# Registrar los viewsets con el router
router.register(r'tipodocumento', TipoDocumentoViewSet)
router.register(r'documento', DocumentoViewSet)

# urlpatterns para incluir las rutas del router
urlpatterns = [
    path('', include(router.urls)),
]