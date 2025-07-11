from django.contrib import admin
from .models import Correspondencia, Recibida, Enviada, AccionCorrespondencia
from .utils import generar_documento_word
from documento.models import Documento
class DocumentoInline(admin.TabularInline):  # O usa StackedInline si prefieres un formato más vertical
    model = Documento
    extra = 1  # Número de formularios vacíos para agregar documentos
    fields = ['archivo','nombre_documento']  # Campos a mostrar del Documento
    fk_name = 'correspondencia'

class CorrespondenciaAdmin(admin.ModelAdmin):
    list_display = ['id_correspondencia', 'fecha_registro', 'referencia','tipo',]  # Campos para listar en la vista de la lista
    inlines = [DocumentoInline]  # Agregamos el Inline para mostrar documentos
    #exclude = ['tipo']  # Excluimos el campo 'tipo' del formulario principal

@admin.register(Enviada)
class EnviadaAdmin(admin.ModelAdmin):
    
    actions = ['accion_generar_documento_word']

    def accion_generar_documento_word(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Solo puedes generar un documento a la vez.", level='error')
            return
        correspondencia_saliente = queryset.first()
        return generar_documento_word(correspondencia_saliente)  # Llamamos a la función importada
    accion_generar_documento_word.short_description = "Generar documento Word"


@admin.register(Recibida)
class RecibidaAdmin(admin.ModelAdmin):
    readonly_fields = ('nro_registro',)
    inlines = [DocumentoInline]  # Agregamos el Inline para documentos en DocEntrante

    
from django import forms
from usuario.models import CustomUser

class AccionCorrespondenciaForm(forms.ModelForm):
    usuarios = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple("Usuarios", is_stacked=False),
        required=False,
        help_text="Puedes seleccionar varios usuarios para derivar la correspondencia"
    )

    class Meta:
        model = AccionCorrespondencia
        fields = ['correspondencia', 'accion', 'observacion', 'usuarios']

    def save(self, commit=True):
        instancia = super().save(commit=False)
        usuarios = self.cleaned_data.get('usuarios')

        # Guardamos la instancia actual sin usuario solo si commit es True y no hay usuarios múltiples
        if commit and not usuarios:
            instancia.save()

        # Si hay múltiples usuarios, crear una instancia por cada uno
        if usuarios:
            for usuario in usuarios:
                AccionCorrespondencia.objects.create(
                    correspondencia=instancia.correspondencia,
                    accion=instancia.accion,
                    observacion=instancia.observacion,
                    usuario=usuario
                )
        return instancia

class AccionCorrespondenciaAdmin(admin.ModelAdmin):
    form = AccionCorrespondenciaForm
    list_display = ['id_accion', 'correspondencia', 'accion', 'usuario', 'fecha']
    list_filter = ['accion', 'fecha']
    search_fields = ['correspondencia__descripcion', 'usuario__username']

    # 👇 Esto es lo más importante para que el campo personalizado 'usuarios' aparezca
    fields = ['correspondencia', 'accion', 'observacion', 'usuarios']

admin.site.register(AccionCorrespondencia, AccionCorrespondenciaAdmin)

# Register your models here.
admin.site.register(Correspondencia, CorrespondenciaAdmin)
