import django_filters
from .models import Contacto, Institucion

class ContactoFilter(django_filters.FilterSet):
    nombre_contacto = django_filters.CharFilter(field_name="nombre_contacto", lookup_expr="icontains")
    apellido_pat_contacto = django_filters.CharFilter(field_name="apellido_pat_contacto", lookup_expr="icontains")
    apellido_mat_contacto = django_filters.CharFilter(field_name="apellido_mat_contacto", lookup_expr="icontains")
    institucion__razon_social = django_filters.CharFilter(field_name="institucion__razon_social", lookup_expr="icontains")
    class Meta:
        model = Contacto
        fields = []

class InstitucionFilter(django_filters.FilterSet):
    razon_social = django_filters.CharFilter(field_name="razon_social", lookup_expr="icontains")
    class Meta:
        model = Institucion
        fields = []
