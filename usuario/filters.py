import django_filters
from django.db.models import Q
from .models import CustomUser

class CustomUserFilter(django_filters.FilterSet):
   nombre_completo = django_filters.CharFilter(method='filter_nombre_completo')
   email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")
   username = django_filters.CharFilter(field_name="username", lookup_expr="icontains")
   institucion__razon_social = django_filters.CharFilter(field_name="institucion__razon_social", lookup_expr="icontains")
   departamento = django_filters.CharFilter(field_name="departamento", lookup_expr="icontains")
   cargo = django_filters.CharFilter(field_name="cargo", lookup_expr="icontains")

   class Meta:
      model = CustomUser
      fields = []

   def filter_nombre_completo(self, queryset, name, value):
      return queryset.filter(
         Q(first_name__icontains=value) |
         Q(last_name__icontains=value) |
         Q(second_name__icontains=value) |
         Q(second_last_name__icontains=value)
      )