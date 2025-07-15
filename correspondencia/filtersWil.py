import django_filters
from .models import Producto

class ProductoFilter(django_filters.FilterSet):
    precio_min = django_filters.NumberFilter(field_name="precio", lookup_expr="gte")
    precio_max = django_filters.NumberFilter(field_name="precio", lookup_expr="lte")
    fecha_creacion_min = django_filters.DateFilter(field_name="fecha_creacion", lookup_expr="gte")
    fecha_creacion_max = django_filters.DateFilter(field_name="fecha_creacion", lookup_expr="lte")
    codigo_barras = django_filters.CharFilter(field_name="codigo_barras", lookup_expr="exact")
    categoria = django_filters.NumberFilter(field_name="categoria__id_categoria")
    proveedor = django_filters.NumberFilter(field_name="id_proveedor__id_proveedor")

    class Meta:
        model = Producto
        fields = []
