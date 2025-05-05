from django.shortcuts import render

# Create your views here.
from .serializers import ContactoSerializer, InstitucionSerializer
from rest_framework import viewsets
from .models import Contacto, Institucion
from gestion_documental.mixins import PaginacionYAllDataMixin

# Create your views here.
class ContactoView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    serializer_class = ContactoSerializer
    queryset = Contacto.objects.all().order_by('id_contacto')

class InstitucionView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    serializer_class = InstitucionSerializer
    queryset = Institucion.objects.all().order_by('id_institucion')