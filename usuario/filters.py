import django_filters
from django.db.models import Q
from .models import CustomUser
from django.db.models import Func
import unicodedata
from django.db.models.functions import Lower

class Unaccent(Func):
    function = "unaccent"

class BaseFilterSet(django_filters.FilterSet):

    @staticmethod
    def _strip_accents(text):
        if text is None:
            return ""
        return "".join(
            c for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )

    def filter_unaccent(self, queryset, field, value):
        if not value:
            return queryset

        value = self._strip_accents(value).lower()

        alias = f"{field.replace('__', '_')}_norm"

        return queryset.annotate(
            **{
                alias: Lower(Unaccent(field))
            }
        ).filter(
            **{
                f"{alias}__icontains": value
            }
        )


class CustomUserFilter(BaseFilterSet):
   nombre_completo = django_filters.CharFilter(method='filter_nombre_completo')
   email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")
   username = django_filters.CharFilter(field_name="username", lookup_expr="icontains")
   institucion__razon_social = django_filters.CharFilter(field_name="institucion__razon_social", lookup_expr="icontains")
   departamento = django_filters.CharFilter(method="filter_departamento")
   cargo = django_filters.CharFilter(field_name="cargo", lookup_expr="icontains")

   class Meta:
      model = CustomUser
      fields = []

   def filter_nombre_completo(self, queryset, name, value):
        if not value:
            return queryset

        palabras = value.split()

        for palabra in palabras:
            queryset = queryset.filter(
                Q(first_name__icontains=palabra)
                | Q(second_name__icontains=palabra)
                | Q(last_name__icontains=palabra)
                | Q(second_last_name__icontains=palabra)
            )

        return queryset
   def filter_departamento(self, queryset, name, value):
        return self.filter_unaccent(queryset, "departamento__nombre", value) #Departamento es un ForeignKey