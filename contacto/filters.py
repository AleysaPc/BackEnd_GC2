import django_filters
from .models import Contacto, Institucion
from django.db.models import Q, Func

class ContactoFilter(django_filters.FilterSet):
    institucion__razon_social = django_filters.CharFilter(field_name="institucion__razon_social", lookup_expr="icontains")
    contacto_nombre_completo = django_filters.CharFilter(method="filter_contacto_nombre_completo")
    class Meta:
        model = Contacto
        fields = []
    def filter_contacto_nombre_completo(self, queryset, name, value):
        if not value:
            return queryset

        palabras = value.split()
        print(palabras)

        for palabra in palabras:
            queryset = queryset.filter(
                Q(nombre_contacto__icontains=palabra)
                | Q(apellido_pat_contacto__icontains=palabra)
                | Q(apellido_mat_contacto__icontains=palabra)
            )

        return queryset

class InstitucionFilter(django_filters.FilterSet):
    razon_social = django_filters.CharFilter(field_name="razon_social", lookup_expr="icontains")
    class Meta:
        model = Institucion
        fields = []
