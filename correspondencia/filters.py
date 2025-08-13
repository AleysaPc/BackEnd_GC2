import django_filters
from .models import Correspondencia, CorrespondenciaElaborada, Enviada, Recibida

class CorrespondenciaFilter(django_filters.FilterSet):
    tipo = django_filters.CharFilter(field_name="tipo", lookup_expr="icontains")
    referencia = django_filters.CharFilter(field_name="referencia", lookup_expr="icontains")
    contacto__nombre_contacto = django_filters.CharFilter(field_name="contacto__nombre_contacto", lookup_expr="icontains")
    contacto__apellido_pat_contacto = django_filters.CharFilter(field_name="contacto__apellido_pat_contacto", lookup_expr="icontains")
    contacto__apellido_mat_contacto = django_filters.CharFilter(field_name="contacto__apellido_mat_contacto", lookup_expr="icontains")
    contacto__institucion__razon_social = django_filters.CharFilter(field_name="contacto__institucion__razon_social", lookup_expr="icontains")
    class Meta:
        model = Correspondencia
        fields = []

class CorrespondenciaElaboradaFilter(django_filters.FilterSet):
    cite = django_filters.CharFilter(field_name="cite", lookup_expr="icontains")
    estado = django_filters.CharFilter(field_name="estado", lookup_expr="icontains")
    estado__in = django_filters.BaseInFilter(field_name='estado', lookup_expr='in')   # nuevo filtro para varios estados, usado en en el frontend en una lista
    referencia = django_filters.CharFilter(field_name="referencia", lookup_expr="icontains")
    contacto__nombre_contacto = django_filters.CharFilter(field_name="contacto__nombre_contacto", lookup_expr="icontains")
    contacto__apellido_pat_contacto = django_filters.CharFilter(field_name="contacto__apellido_pat_contacto", lookup_expr="icontains")
    contacto__apellido_mat_contacto = django_filters.CharFilter(field_name="contacto__apellido_mat_contacto", lookup_expr="icontains")
    contacto__institucion__razon_social = django_filters.CharFilter(field_name="contacto__institucion__razon_social", lookup_expr="icontains")
    class Meta:
        model = CorrespondenciaElaborada
        fields = []
    
class EnviadaFilter(django_filters.FilterSet):
    cite = django_filters.CharFilter(field_name="cite", lookup_expr="icontains")
    referencia = django_filters.CharFilter(field_name="referencia", lookup_expr="icontains")
    contacto__nombre_contacto = django_filters.CharFilter(field_name="contacto__nombre_contacto", lookup_expr="icontains")
    contacto__apellido_pat_contacto = django_filters.CharFilter(field_name="contacto__apellido_pat_contacto", lookup_expr="icontains")
    contacto__apellido_mat_contacto = django_filters.CharFilter(field_name="contacto__apellido_mat_contacto", lookup_expr="icontains")
    contacto__institucion__razon_social = django_filters.CharFilter(field_name="contacto__institucion__razon_social", lookup_expr="icontains")
 
    class Meta:
        model = Enviada
        fields = []

class RecibidaFilter(django_filters.FilterSet):
    nro_registro = django_filters.CharFilter(field_name="nro_registro", lookup_expr="icontains")
    referencia = django_filters.CharFilter(field_name="referencia", lookup_expr="icontains")
    contacto__nombre_contacto = django_filters.CharFilter(field_name="contacto__nombre_contacto", lookup_expr="icontains")
    contacto__apellido_pat_contacto = django_filters.CharFilter(field_name="contacto__apellido_pat_contacto", lookup_expr="icontains")
    contacto__apellido_mat_contacto = django_filters.CharFilter(field_name="contacto__apellido_mat_contacto", lookup_expr="icontains")
    contacto__institucion__razon_social = django_filters.CharFilter(field_name="contacto__institucion__razon_social", lookup_expr="icontains")
    
 
    class Meta:
        model = Recibida
        fields = []