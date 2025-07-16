import django_filters
from .models import CorrespondenciaElaborada, Enviada

class CorrespondenciaElaboradaFilter(django_filters.FilterSet):
    cite = django_filters.CharFilter(field_name="cite", lookup_expr="icontains")
    estado = django_filters.CharFilter(field_name="estado", lookup_expr="icontains")
    class Meta:
        model = CorrespondenciaElaborada
        fields = []
    
class EnviadaFilter(django_filters.FilterSet):
    cite = django_filters.CharFilter(field_name="cite", lookup_expr="icontains")
    estado = django_filters.CharFilter(field_name="estado", lookup_expr="icontains")
    class Meta:
        model = Enviada
        fields = []