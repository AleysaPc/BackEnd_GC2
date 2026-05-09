from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import AlertaVencimiento

@admin.register(AlertaVencimiento)
class AlertaVencimientoAdmin(admin.ModelAdmin):
    list_display = [
        'correspondencia', 
        'usuario_responsable', 
        'tipo_alerta', 
        'nivel_alerta',
        'vista',
        'fecha_alerta',
        'fecha_vista',
        'get_color_estado'
    ]
    list_filter = [
        'tipo_alerta',
        'nivel_alerta', 
        'vista',
        'fecha_alerta'
    ]
    search_fields = [
        'correspondencia__referencia',
        'usuario_responsable__email'
    ]
    readonly_fields = [
        'fecha_alerta',
        'get_color_estado'
    ]
    
    def get_color_estado(self, obj):
        return obj.get_color_estado()
    get_color_estado.short_description = 'Color'