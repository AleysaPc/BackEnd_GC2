from django.db import models
from django.utils.timezone import now
from django.db import models, transaction
from django.db.models import Max

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

class DocEntrante(Correspondencia):
    nro_registro = models.CharField(max_length=50, unique=True, blank=True, null=True)
    fecha_recepcion = models.DateTimeField(blank=True, null=True)
    fecha_respuesta = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.nro_registro:
            with transaction.atomic():
                ultimo = DocEntrante.objects.order_by('-id_correspondencia').first()  # Usa el campo 'id' heredado de Correspondencia
                
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

class DocSaliente(Correspondencia):
    cite = models.CharField(max_length=50, blank=True, null=True)
    fecha_envio = models.DateTimeField(blank=True, null=True)
    fecha_recepcion = models.DateTimeField(blank=True, null=True)
    fecha_seguimiento = models.DateTimeField(blank=True, null=True)
    archivo_word = models.FileField(upload_to='documentos_borrador/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.cite:
            with transaction.atomic():
                ultimo = DocSaliente.objects.order_by('-id_correspondencia').first()  # Usa el campo 'id' heredado de Correspondencia
                
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

class DocInterno(Correspondencia):
    numero = models.PositiveIntegerField(editable=False)  # Número secuencial único
    gestion = models.PositiveIntegerField(default=now().year, editable=False)  # Año de gestión
    cite = models.CharField(max_length=100, unique=True, blank=True)  # Código único del documento
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.cite} "
