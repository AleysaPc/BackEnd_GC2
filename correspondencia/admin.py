from django.contrib import admin
from .models import Correspondencia, DocEntrante, DocSaliente
from .utils import generar_documento_word
from documento.models import Documento
class DocumentoInline(admin.TabularInline):  # O usa StackedInline si prefieres un formato más vertical
    model = Documento
    extra = 1  # Número de formularios vacíos para agregar documentos
    fields = ['archivo','nombre_documento', 'tipo_documento', ]  # Campos a mostrar del Documento
    fk_name = 'correspondencia'

class CorrespondenciaAdmin(admin.ModelAdmin):
    list_display = ['id_correspondencia', 'fecha_registro', 'referencia','tipo',]  # Campos para listar en la vista de la lista
    inlines = [DocumentoInline]  # Agregamos el Inline para mostrar documentos
    #exclude = ['tipo']  # Excluimos el campo 'tipo' del formulario principal

@admin.register(DocSaliente)
class DocSalienteAdmin(admin.ModelAdmin):
    
    actions = ['accion_generar_documento_word']

    def accion_generar_documento_word(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Solo puedes generar un documento a la vez.", level='error')
            return
        correspondencia_saliente = queryset.first()
        return generar_documento_word(correspondencia_saliente)  # Llamamos a la función importada
    accion_generar_documento_word.short_description = "Generar documento Word"


@admin.register(DocEntrante)
class DocEntranteAdmin(admin.ModelAdmin):
    readonly_fields = ('nro_registro',)
    inlines = [DocumentoInline]  # Agregamos el Inline para documentos en DocEntrante

    

# Register your models here.
admin.site.register(Correspondencia, CorrespondenciaAdmin)
