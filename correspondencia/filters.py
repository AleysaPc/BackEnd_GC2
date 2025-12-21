from cgitb import lookup
from dataclasses import field
import django_filters
from django.db.models import Q
from .models import Correspondencia, CorrespondenciaElaborada, Enviada, Recibida

class CorrespondenciaFilter(django_filters.FilterSet):
    tipo = django_filters.CharFilter(field_name="tipo", lookup_expr="icontains")
    referencia = django_filters.CharFilter(field_name="referencia", lookup_expr="icontains")
    contacto_nombre_completo = django_filters.CharFilter(method='filter_contacto_nombre_completo')
    contacto__institucion__razon_social = django_filters.CharFilter(field_name="contacto__institucion__razon_social", lookup_expr="icontains")
    class Meta:
        model = Correspondencia
        fields = []

    def filter_contacto_nombre_completo(self, queryset, name, value):
        return queryset.filter(
            Q(contacto__nombre_contacto__icontains=value) |
            Q(contacto__apellido_pat_contacto__icontains=value) |
            Q(contacto__apellido_mat_contacto__icontains=value)
        )

class CorrespondenciaElaboradaFilter(django_filters.FilterSet):
    cite = django_filters.CharFilter(field_name="cite", lookup_expr="icontains")
    estado = django_filters.CharFilter(field_name="estado", lookup_expr="icontains")
    estado__in = django_filters.BaseInFilter(field_name='estado', lookup_expr='in')
    referencia = django_filters.CharFilter(field_name="referencia", lookup_expr="icontains")
    contacto_nombre_completo = django_filters.CharFilter(method='filter_contacto_nombre_completo')
    contacto__institucion__razon_social = django_filters.CharFilter(field_name="contacto__institucion__razon_social", lookup_expr="icontains")
    plantilla__nombre_plantilla = django_filters.CharFilter(field_name="plantilla__nombre_plantilla", lookup_expr="icontains")
    email = django_filters.CharFilter(field_name='usuario__email', lookup_expr='icontains')
    ambito = django_filters.CharFilter(field_name="ambito", lookup_expr="icontains")
    
    class Meta:
        model = CorrespondenciaElaborada
        fields = []

    def filter_contacto_nombre_completo(self, queryset, name, value):
        return queryset.filter(
            Q(contacto__nombre_contacto__icontains=value) |
            Q(contacto__apellido_pat_contacto__icontains=value) |
            Q(contacto__apellido_mat_contacto__icontains=value)
        )
    
class EnviadaFilter(django_filters.FilterSet):
    cite = django_filters.CharFilter(field_name="cite", lookup_expr="icontains")
    referencia = django_filters.CharFilter(field_name="referencia", lookup_expr="icontains")
    contacto_nombre_completo = django_filters.CharFilter(method='filter_contacto_nombre_completo')
    contacto__institucion__razon_social = django_filters.CharFilter(field_name="contacto__institucion__razon_social", lookup_expr="icontains")
 
    class Meta:
        model = Enviada
        fields = []
    
    def filter_contacto_nombre_completo(self, queryset, name, value):
        return queryset.filter(
            Q(contacto__nombre_contacto__icontains=value) |
            Q(contacto__apellido_pat_contacto__icontains=value) |
            Q(contacto__apellido_mat_contacto__icontains=value)
        )

class RecibidaFilter(django_filters.FilterSet):
    nro_registro = django_filters.CharFilter(field_name="nro_registro", lookup_expr="icontains")
    referencia = django_filters.CharFilter(field_name="referencia", lookup_expr="icontains")
    contacto__institucion__razon_social = django_filters.CharFilter(field_name="contacto__institucion__razon_social", lookup_expr="icontains")

    class Meta:
        model = Recibida
        fields = []
    