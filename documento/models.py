from django.db import models
import os
from django.contrib.postgres.fields import ArrayField



# Create your models here.
class TipoDocumentoInterno(models.Model):
    id_tipo_documento_interno = models.AutoField(primary_key=True)
    nombre_documento_interno = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre_documento_interno

class TipoDocumento(models.Model):
    id_tipo_documento = models.AutoField(primary_key=True)
    nombre_tipo_documento = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre_tipo_documento


def ruta_archivo(instance, filename):
    tipo = instance.correspondencia.tipo if instance.correspondencia else 'otros'
    if tipo == 'enviado':
        return os.path.join('documentos', 'enviados', filename)
    elif tipo == 'recibido':
        return os.path.join('documentos', 'recibido', filename)
    else:
        return os.path.join('documentos', 'otros', filename)
    
class Documento(models.Model):
    id_documento = models.AutoField(primary_key=True)
    nombre_documento = models.CharField(max_length=255, blank=True)
    archivo = models.FileField(upload_to=ruta_archivo, blank=True, null=True)  # Cambia la ruta según tu estructura de carpetas
    fecha_subida = models.DateTimeField(auto_now_add=True)
    correspondencia = models.ForeignKey('correspondencia.Correspondencia', on_delete=models.CASCADE, related_name='documentos') 
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE, related_name='documentos',)
    tipo_documento_interno = models.ForeignKey(TipoDocumentoInterno, on_delete=models.CASCADE, related_name='documentos_internos', blank=True, null=True)
    def __str__(self):
        return self.nombre_documento
    
class vectorDocumento(models.Model):
    id_vector = models.AutoField(primary_key=True)
    vector = ArrayField(models.FloatField(), blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='vectores', null=True, blank=True)

    def __str__(self):
        return f"Vector {self.id_vector} for {self.documento.nombre_documento if self.documento else 'No Document'}"