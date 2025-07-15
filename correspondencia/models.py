from django.db import models
from django.utils.timezone import now
from django.db import models, transaction
from django.db.models import Max
from documento.models import PlantillaDocumento

class Correspondencia(models.Model):
    TIPO_CHOICES_ESTADO = [('borrador', 'Borrador'), ('en_revision', 'En revisión'), ('aprobado', 'Aprobado'), ('rechazado', 'Rechazado')]
    TIPO_CHOICES_PRIORIDAD = [('alta', 'Alta'), ('media', 'Media'), ('baja', 'Baja')]
    TIPO_CHOICES = [('recibido', 'Recibido'), ('enviado', 'Enviado')]
    id_correspondencia = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    referencia = models.CharField(max_length=255)
    descripcion = models.TextField()
    paginas = models.IntegerField()
    prioridad = models.CharField(max_length=20, choices=TIPO_CHOICES_PRIORIDAD)
    estado = models.CharField(max_length=20, choices=TIPO_CHOICES_ESTADO)
    comentario = models.TextField(null=True, blank=True)
    contacto = models.ForeignKey('contacto.Contacto', on_delete=models.CASCADE, blank=True, null=True)
    usuario = models.ForeignKey('usuario.CustomUser', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.referencia} - {self.tipo}"

class Recibida(Correspondencia):
    nro_registro = models.CharField(max_length=50, unique=True, blank=True, null=True)
    fecha_recepcion = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.nro_registro:
            with transaction.atomic():
                ultimo = Recibida.objects.order_by('-id_correspondencia').first()  # Usa el campo 'id' heredado de Correspondencia
                
                if ultimo and ultimo.nro_registro:
                    try:
                        numero_actual = int(ultimo.nro_registro.split('-')[1])
                    except (IndexError, ValueError):
                        numero_actual = 0
                else:
                    numero_actual = 0

                nuevo_numero = numero_actual + 1
                self.nro_registro = f"Reg-{nuevo_numero:03}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nro_registro}"

class Enviada(Correspondencia):
    cite = models.CharField(max_length=50, blank=True, null=True)
    fecha_envio = models.DateTimeField(blank=True, null=True)
    fecha_recepcion = models.DateTimeField(blank=True, null=True)
    fecha_seguimiento = models.DateTimeField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.cite:
            with transaction.atomic():
                ultimo = Enviada.objects.order_by('-id_correspondencia').first()  # Usa el campo 'id' heredado de Correspondencia
                
                if ultimo and ultimo.cite:
                    try:
                        numero_actual = int(ultimo.cite.rsplit('-', 1)[1])
                    except (IndexError, ValueError):
                        numero_actual = 0
                else:
                    numero_actual = 0

                nuevo_numero = numero_actual + 1
                self.cite = f"FSTL-FTA/DPTO/LP/-{nuevo_numero:03}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cite}"

# correspondencia/models.py

from django.db import models, transaction
from django.utils.timezone import now
from jinja2 import Template

def renderizar_contenido_html(estructura_html, context):
    template = Template(estructura_html)
    return template.render(context)

class CorrespondenciaElaborada(Correspondencia):
    plantilla = models.ForeignKey(
        PlantillaDocumento,
        on_delete=models.PROTECT,
        related_name='correspondencias',
        null=True,
        blank=True,
        help_text="Plantilla para generación del documento"
    )
    sigla = models.CharField(max_length=50, default='FSTL-FTA')
    numero = models.PositiveIntegerField(editable=False)
    gestion = models.PositiveIntegerField(default=now().year, editable=False)
    cite = models.CharField(max_length=100, unique=True, blank=True)
    contenido_html = models.TextField(blank=True, null=True)
    firmado = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        if not self.numero:
            with transaction.atomic():
                ultimo = CorrespondenciaElaborada.objects.filter(
                    gestion=self.gestion,
                    plantilla=self.plantilla
                ).order_by('-numero').first()
                self.numero = (ultimo.numero + 1) if ultimo else 1

        if not self.cite:
            sigla_tipo = self.plantilla.tipo.upper() if self.plantilla else 'OTRO'
            self.cite = f"{self.sigla}/{sigla_tipo}/{self.gestion}-{self.numero:03}"

        # 👇 Generar el HTML si no existe
        if not self.contenido_html and self.plantilla and self.plantilla.estructura_html:
            context = {
                "referencia": self.referencia,
                "descripcion": self.descripcion,
                "asunto": self.referencia,  # Puedes personalizar si manejas asunto por separado
                "nombre_destinatario": self.contacto.nombre_contacto if self.contacto else "",
                "cite": self.cite,
                "fecha": self.fecha_registro.strftime("%d/%m/%Y") if self.fecha_registro else "",
                "gestion": self.gestion,
                "prioridad": self.prioridad,
                # Otros campos según tu plantilla
            }
            self.contenido_html = renderizar_contenido_html(self.plantilla.estructura_html, context)

        super().save(*args, **kwargs)



class AccionCorrespondencia(models.Model):
    id_accion = models.AutoField(primary_key=True)
    correspondencia = models.ForeignKey('Correspondencia', on_delete=models.CASCADE, related_name='acciones')
    usuario = models.ForeignKey('usuario.CustomUser', on_delete=models.CASCADE, blank=True, null=True)
    accion = models.CharField(max_length=50)  # Derivar, Archivar, Rechazar, etc.
    observacion = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.accion} por {self.usuario} el {self.fecha}"
