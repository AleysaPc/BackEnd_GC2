from correspondencia.services.renderizado import generar_html_desde_objeto
from django.db import models
from django.utils.timezone import now
from django.db import models, transaction
from django.db.models import Max
from documento.models import PlantillaDocumento
from jinja2 import Template

class Correspondencia(models.Model):
    TIPO_CHOICES_ESTADO = [('borrador', 'Borrador'), ('en_revision', 'En revisión'), ('aprobado', 'Aprobado'), ('rechazado', 'Rechazado'), ('enviado', 'Enviado')]
    TIPO_CHOICES_PRIORIDAD = [('alta', 'Alta'), ('media', 'Media'), ('baja', 'Baja')]
    TIPO_CHOICES = [('recibido', 'Recibido'), ('enviado', 'Enviado')]
    id_correspondencia = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    referencia = models.CharField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    paginas = models.IntegerField(default=1)
    prioridad = models.CharField(max_length=20, choices=TIPO_CHOICES_PRIORIDAD)
    estado = models.CharField(max_length=20, choices=TIPO_CHOICES_ESTADO)
    contacto = models.ForeignKey('contacto.Contacto', on_delete=models.CASCADE, blank=True, null=True)
    usuario = models.ForeignKey('usuario.CustomUser', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.referencia} - {self.tipo}"

class Recibida(Correspondencia):
    nro_registro = models.CharField(max_length=50, unique=True, blank=True, null=True)
    fecha_recepcion = models.DateField(blank=False, null=False)
    hora_recepcion = models.TimeField(blank=False, null=False)
    fecha_respuesta = models.DateField(blank=True, null=True)
    hora_respuesta = models.TimeField(blank=True, null=True)

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
    fecha_envio = models.DateField(blank=True, null=True)
    hora_envio = models.TimeField(blank=True, null=True)
    fecha_recepcion = models.DateField(blank=True, null=True)
    hora_recepcion = models.TimeField(blank=True, null=True)
    fecha_seguimiento = models.DateTimeField(blank=True, null=True)
    

    def __str__(self):
        return f"{self.cite}"

# correspondencia/models.py


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
    fecha_envio = models.DateField(null=True, blank=True)
    hora_envio = models.TimeField(null=True, blank=True)
    fecha_recepcion = models.DateField(null=True, blank=True)
    hora_recepcion = models.TimeField(null=True, blank=True)
    fecha_seguimiento = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    fecha_elaboracion = models.DateTimeField(auto_now_add=True)
    respuesta_a = models.ForeignKey(
        Recibida,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='respuestas',
        help_text="Nota recibida a la que responde esta nota elaborada"
    )
    def generar_contenido_html(self):
        self.contenido_html = generar_html_desde_objeto(self)

    def save(self, *args, **kwargs):
        if not self.numero:
            with transaction.atomic():
                ultimo = CorrespondenciaElaborada.objects.filter(
                    gestion=self.gestion,
                    plantilla=self.plantilla
                ).order_by('-numero').first()
                self.numero = (ultimo.numero + 1) if ultimo else 1

        if not self.cite:
            if self.plantilla:
                if self.plantilla.tipo == 'nota_externa':
                    sigla_tipo = 'NE'
                else:
                    sigla_tipo = self.plantilla.tipo.upper()
            else:
                sigla_tipo = 'OTRO'
            self.cite = f"{self.sigla}/{sigla_tipo}/{self.gestion}-{self.numero:03}"

        # ✅ Generar HTML siempre, incluso si ya existe uno anterior
        self.generar_contenido_html()

        # Guardar con contenido_html actualizado
        super().save(*args, **kwargs)


class AccionCorrespondencia(models.Model):

    ACCIONES = [
        ('DERIVADO', 'Derivado'),
        ('VISTO', 'Visto'),
        ('OBSERVADO', 'Observado'),
        ('APROBADO', 'Aprobado'),
    ]
    id_accion = models.AutoField(primary_key=True)
    correspondencia = models.ForeignKey('Correspondencia', on_delete=models.CASCADE, related_name='acciones')
    usuario = models.ForeignKey('usuario.CustomUser', on_delete=models.CASCADE, blank=True, null=True)
    usuario_destino = models.ForeignKey('usuario.CustomUser', on_delete=models.CASCADE, blank=True, null=True, related_name='acciones_destino')
    accion = models.CharField(max_length=50, choices=ACCIONES)  # Derivar, Archivar, Rechazar, etc.
    comentario = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']