from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactoView, InstitucionView, InstitucionSelectView

#Creamos el router y registramos los viewsets
router = DefaultRouter()

# Registrar los viewsets con el router
router.register(r'contacto', ContactoView)
router.register(r'institucion', InstitucionView)

urlpatterns = [
    path('', include(router.urls)),

    path('institucion-select/', InstitucionSelectView.as_view(), name='institucion-select'),
]