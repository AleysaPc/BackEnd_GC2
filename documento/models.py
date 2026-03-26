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
    archivo = models.FileField(upload_to=ruta_archivo, blank=True, null=True)
    
    # === CAMPOS NUEVOS PARA BASE64 ===
    archivo_data = models.TextField(null=True, blank=True, help_text="Archivo en formato base64")
    archivo_nombre = models.CharField(max_length=255, null=True, blank=True, help_text="Nombre original del archivo")
    
    fecha_subida = models.DateTimeField(auto_now_add=True)
    correspondencia = models.ForeignKey('correspondencia.Correspondencia', on_delete=models.CASCADE, related_name='documentos') 
    vector_embedding = VectorField(dimensions=384, null=True, blank=True)
    contenido_extraido = models.TextField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Guardar archivo como base64 si existe y no está guardado
        if self.archivo and not self.archivo_data:
            try:
                self.archivo_data = self.file_to_base64()
                self.archivo_nombre = self.archivo.name
                print(f"✅ Archivo convertido a base64: {self.archivo_nombre}")
            except Exception as e:
                print(f"❌ Error convirtiendo a base64: {str(e)}")
        
        # Guardar el modelo
        super().save(*args, **kwargs)
        
        # Iniciar procesamiento si hay archivo_data y no está procesado
        if self.archivo_data and not self.contenido_extraido:
            from documento.busquedaSemantica.procesar_documento import procesar_documento
            # Pasar el ID en lugar de la ruta
            procesar_documento(self.id, async_processing=True)
    
    def file_to_base64(self):
        """Convertir archivo a base64"""
        import base64
        self.archivo.seek(0)
        return base64.b64encode(self.archivo.read()).decode('utf-8')
    
    def get_archivo_temporal(self):
        """Crear archivo temporal para OCR desde base64"""
        import base64
        import tempfile
        import os
        
        if self.archivo_data:
            try:
                # Decodificar base64
                file_data = base64.b64decode(self.archivo_data)
                
                # Crear archivo temporal con extensión correcta
                ext = os.path.splitext(self.archivo_nombre)[1]
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                temp_file.write(file_data)
                temp_file.close()
                
                print(f"✅ Archivo temporal creado: {temp_file.name}")
                return temp_file.name
            except Exception as e:
                print(f"❌ Error creando archivo temporal: {str(e)}")
                return None
        
        return None

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