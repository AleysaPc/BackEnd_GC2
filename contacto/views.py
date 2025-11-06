from django.shortcuts import render

# Create your views here.
from .serializers import ContactoSerializer, InstitucionSerializer
from rest_framework import viewsets
from .models import Contacto, Institucion
from gestion_documental.mixins import PaginacionYAllDataMixin
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ContactoFilter, InstitucionFilter
from rest_framework import filters
# Create your views here.
class ContactoView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    serializer_class = ContactoSerializer
    queryset = Contacto.objects.all().order_by('id_contacto')

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = ContactoFilter
    search_fields = [
        'nombre_contacto', 'apellido_pat_contacto', 'apellido_mat_contacto', 'institucion__razon_social'
    ]
    ordering_fields = ['nombre_contacto', 'apellido_pat_contacto', 'apellido_mat_contacto', 'institucion__razon_social']

class InstitucionView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    serializer_class = InstitucionSerializer
    queryset = Institucion.objects.all().order_by('id_institucion')

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = InstitucionFilter
    search_fields = [
        'razon_social'
    ]
    ordering_fields = ['razon_social']