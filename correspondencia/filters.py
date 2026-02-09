
import unicodedata
import django_filters
from django.db.models import Q, Func
from django.db.models.functions import Lower

from .models import Correspondencia, CorrespondenciaElaborada, Enviada, Recibida


class Unaccent(Func):
    function = "unaccent"


class CorrespondenciaFilter(django_filters.FilterSet):
    tipo = django_filters.CharFilter(field_name="tipo", lookup_expr="icontains")
    referencia = django_filters.CharFilter(field_name="referencia", lookup_expr="icontains")
    estado = django_filters.CharFilter(field_name="estado", lookup_expr="icontains")
    estado__in = django_filters.BaseInFilter(field_name="estado", lookup_expr="in")
    contacto_nombre_completo = django_filters.CharFilter(method="filter_contacto_nombre_completo")
    contacto__institucion__razon_social = django_filters.CharFilter(
        field_name="contacto__institucion__razon_social", lookup_expr="icontains"
    )

    class Meta:
        model = Correspondencia
        fields = []

    def filter_contacto_nombre_completo(self, queryset, name, value):
        return queryset.filter(
            Q(contacto__nombre_contacto__icontains=value)
            | Q(contacto__apellido_pat_contacto__icontains=value)
            | Q(contacto__apellido_mat_contacto__icontains=value)
        )


class CorrespondenciaElaboradaFilter(django_filters.FilterSet):
    cite = django_filters.CharFilter(field_name="cite", lookup_expr="icontains")
    estado = django_filters.CharFilter(field_name="estado", lookup_expr="icontains")
    estado__in = django_filters.BaseInFilter(field_name="estado", lookup_expr="in")
    referencia = django_filters.CharFilter(field_name="referencia", lookup_expr="icontains")
    contacto_nombre_completo = django_filters.CharFilter(method="filter_contacto_nombre_completo")
    contacto__institucion__razon_social = django_filters.CharFilter(
        field_name="contacto__institucion__razon_social", lookup_expr="icontains"
    )
    plantilla__nombre_plantilla = django_filters.CharFilter(
        field_name="plantilla__nombre_plantilla", lookup_expr="icontains"
    )
    plantilla__tipo = django_filters.CharFilter(method="filter_plantilla_tipo")
    email = django_filters.CharFilter(field_name="usuario__email", lookup_expr="icontains")
    ambito = django_filters.CharFilter(field_name="ambito", lookup_expr="icontains")
    destino_interno = django_filters.CharFilter(method="filter_destino_interno")

    class Meta:
        model = CorrespondenciaElaborada
        fields = []

    def filter_contacto_nombre_completo(self, queryset, name, value):
        return queryset.filter(
            Q(contacto__nombre_contacto__icontains=value)
            | Q(contacto__apellido_pat_contacto__icontains=value)
            | Q(contacto__apellido_mat_contacto__icontains=value)
        )

    @staticmethod
    def _strip_accents(text):
        if text is None:
            return ""
        return "".join(
            c for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )

    def filter_plantilla_tipo(self, queryset, name, value):
        # Búsqueda sin distinción de tildes y mayúsculas/minúsculas
        if not value:
            return queryset
        value_norm = self._strip_accents(value).lower()
        return queryset.annotate(
            _tipo_norm=Lower(Unaccent("plantilla__tipo"))
        ).filter(
            _tipo_norm__icontains=value_norm
        )


    def filter_destino_interno(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(destino_interno__first_name__icontains=value)
            | Q(destino_interno__second_name__icontains=value)
            | Q(destino_interno__last_name__icontains=value)
            | Q(destino_interno__second_last_name__icontains=value)
            | Q(destino_interno__email__icontains=value)
            | Q(destino_interno__departamento__nombre__icontains=value)
            | Q(destino_interno__departamento__sigla__icontains=value)
        )


class EnviadaFilter(django_filters.FilterSet):
    cite = django_filters.CharFilter(field_name="cite", lookup_expr="icontains")
    referencia = django_filters.CharFilter(field_name="referencia", lookup_expr="icontains")
    contacto_nombre_completo = django_filters.CharFilter(method="filter_contacto_nombre_completo")
    contacto__institucion__razon_social = django_filters.CharFilter(
        field_name="contacto__institucion__razon_social", lookup_expr="icontains"
    )

    class Meta:
        model = Enviada
        fields = []

    def filter_contacto_nombre_completo(self, queryset, name, value):
        return queryset.filter(
            Q(contacto__nombre_contacto__icontains=value)
            | Q(contacto__apellido_pat_contacto__icontains=value)
            | Q(contacto__apellido_mat_contacto__icontains=value)
        )


class RecibidaFilter(django_filters.FilterSet):
    nro_registro = django_filters.CharFilter(field_name="nro_registro", lookup_expr="icontains")
    referencia = django_filters.CharFilter(field_name="referencia", lookup_expr="icontains")
    contacto__institucion__razon_social = django_filters.CharFilter(
        field_name="contacto__institucion__razon_social", lookup_expr="icontains"
    )

    class Meta:
        model = Recibida
        fields = []
