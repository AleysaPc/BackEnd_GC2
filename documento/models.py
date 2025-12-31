from django.db import models
import os
from pgvector.django import VectorField

def ruta_archivo(instance, filename):
    tipo = instance.correspondencia.tipo if instance.correspondencia else 'otros'
    try:
        sindicato = instance.correspondencia.contacto.institucion.razon_social
        sindicato = sindicato.replace(" ", "_").replace("/", "-")  # Limpieza de nombre
    except AttributeError:
        sindicato = "desconocido"
    anio = instance.correspondencia.fecha_registro.year if instance.correspondencia and instance.correspondencia.fecha_registro else "sin_fecha"
    return os.path.join('documentos', sindicato, tipo, str(anio), filename)

    
class Documento(models.Model):
    id_documento = models.AutoField(primary_key=True)
    nombre_documento = models.CharField(max_length=255, blank=True)
    archivo = models.FileField(upload_to=ruta_archivo, blank=True, null=True)  # Cambia la ruta según tu estructura de carpetas
    fecha_subida = models.DateTimeField(auto_now_add=True)
    correspondencia = models.ForeignKey('correspondencia.Correspondencia', on_delete=models.CASCADE, related_name='documentos') 
    vector_embedding = VectorField(dimensions=384, null=True, blank=True)  # Usa 384 o 768 según tu modelo
    contenido_extraido = models.TextField(blank=True, null=True)  # ← Texto plano del PDF
    
    def save(self, *args, **kwargs):
        from .busquedaSemantica.procesamiento import procesar_documento
        super().save(*args, **kwargs)
        if self.archivo and not self.contenido_extraido:
            procesar_documento(self.nombre_documento, self.archivo.path)

TIPO_DOCUMENTO_CHOICES = [
    ('comunicado', 'Comunicado'),
    ('convocatoria', 'Convocatoria'),
    ('resolucion', 'Resolución'),
    ('informe', 'Informe'),
    ('memorando', 'Memorando'),
    ('nota', 'Nota'),
]

class PlantillaDocumento(models.Model):
    id_plantilla = models.AutoField(primary_key=True)
    nombre_plantilla = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    estructura_html = models.TextField(blank=True, null=True)  # Plantilla Jinja2
    tipo = models.CharField(max_length=50, choices=TIPO_DOCUMENTO_CHOICES)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre_plantilla} ({self.get_tipo_display()})"
