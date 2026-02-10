from tokenize import blank_re
from django.db import models
from django.utils.timezone import now
from django.db import models, transaction
from django.db.models import Max
from jinja2 import Template
import html
import re
from sentence_transformers import SentenceTransformer
from pgvector.django import VectorField

_sbert_model = None

def _get_sbert_model():
    global _sbert_model
    if _sbert_model is None:
        _sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _sbert_model

def _strip_html_to_text(value):
    if not value:
        return ""
    # Remove tags and decode HTML entities.
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    # Collapse whitespace.
    return " ".join(text.split())

def _build_semantic_text(instance):
    parts = [
        instance.referencia,
        instance.descripcion_introduccion,
        instance.descripcion_desarrollo,
        instance.descripcion_conclusion,
    ]
    cleaned = [_strip_html_to_text(p) for p in parts if p]
    if cleaned:
        return " ".join(cleaned)
    # Fallback: use full HTML if no structured content available.
    return _strip_html_to_text(instance.contenido_html or "")

class Correspondencia(models.Model):
    # Estados globales del documento en un solo lugar (alineados con acciones).
    TIPO_CHOICES_ESTADO = [
        ('borrador', 'Borrador'),
        ('en_revision', 'En revisión'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('enviado', 'Enviado'),
        ('archivado', 'Archivado'),
        ('derivado', 'Derivado'),
        ('observado', 'Observado'),
        ('devuelto', 'Devuelto'),
    ]
    TIPO_CHOICES_PRIORIDAD = [('alta', 'Alta'), ('media', 'Media'), ('baja', 'Baja')]
    TIPO_CHOICES = [('recibido', 'Recibido'), ('enviado', 'Enviado')]
    id_correspondencia = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    referencia = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(null=True, blank=True)
    paginas = models.IntegerField(default=1)
    prioridad = models.CharField(max_length=20, choices=TIPO_CHOICES_PRIORIDAD)
    estado = models.CharField(max_length=20, choices=TIPO_CHOICES_ESTADO)
    contacto = models.ForeignKey('contacto.Contacto', on_delete=models.CASCADE, blank=True, null=True)
    usuario = models.ForeignKey('usuario.CustomUser', on_delete=models.CASCADE, blank=True, null=True)
    estado_actual = models.CharField(max_length=50, default='REGISTRADO',help_text="Último estado del documento (Ej: Derivado, En proceso, Archivado, Finalizado)")
    ultima_modificacion = models.DateTimeField(auto_now=True, help_text="Fecha y hora de la última acción o modificación registrada")
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-fecha_registro']
        
    def __str__(self):
        return f"{self.referencia} - {self.tipo}"

class Recibida(Correspondencia):
    nro_registro = models.CharField(max_length=50, unique=True, blank=True, null=True)
    fecha_recepcion = models.DateTimeField(blank=False, null=False)
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

class PreSelloRecibida(models.Model):
    pre_nro_registro = models.CharField(max_length=20, unique=True)
    usuario = models.ForeignKey('usuario.CustomUser', on_delete=models.CASCADE, blank=True, null=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.pre_nro_registro
        
class Enviada(Correspondencia):
    cite = models.CharField(max_length=50, blank=True, null=True)
    fecha_envio = models.DateTimeField(blank=True, null=True)
    fecha_recepcion = models.DateTimeField(blank=True, null=True)
    fecha_seguimiento = models.DateTimeField(blank=True, null=True)
    

    def __str__(self):
        return f"{self.cite}"

# correspondencia/models.py


def renderizar_contenido_html(estructura_html, context):
    template = Template(estructura_html)
    return template.render(context)

class CorrespondenciaElaborada(Correspondencia):
    AMBITO_CHOICES = [('interno', 'Interno'), ('externo','Externo')]
    ambito = models.CharField(max_length=20, choices=AMBITO_CHOICES, blank=True, null=True )
    plantilla = models.ForeignKey(
        'documento.PlantillaDocumento',  # Usando notación de cadena para la referencia
        on_delete=models.SET_NULL,
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
    vector_embedding_html = VectorField(dimensions=384, null=True, blank=True)
    firmado = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_recepcion = models.DateTimeField(null=True, blank=True)
    fecha_seguimiento = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    fecha_elaboracion = models.DateTimeField(auto_now_add=True)
    descripcion_introduccion = models.TextField(blank=True, null=True)
    descripcion_desarrollo = models.TextField(blank=True, null=True)
    descripcion_conclusion = models.TextField(blank=True, null=True)
    respuesta_a = models.ForeignKey(
        Recibida,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='respuestas',
        help_text="Nota recibida a la que responde esta nota elaborada"
    )
    estado_entrega = models.CharField(
        max_length=30,
        choices=[
            ("pendiente", "Pendiente"),
            ("entregado", "Entregado"),
            ("no_entregado", "No entregado"),
            ("devuelto", "Devuelto"),
            ("rechazado", "Rechazado"),
            ("extraviado", "Extraviado"),
            ("direccion_incorrecta", "Dirección incorrecta"),
            ("destinatario_incorrecto","Destinatario incorrecto")
        ],
        default="pendiente"
    )

    motivo_no_entrega = models.TextField(blank=True, null=True)
    fecha_intento_entrega = models.DateTimeField(blank=True, null=True)
    numero_intentos = models.PositiveIntegerField(default=0)
    destino_interno = models.ForeignKey('usuario.CustomUser', on_delete=models.SET_NULL, blank=True, null=True)

    def generar_contenido_html(self):
        from correspondencia.services.renderizado import generar_html_desde_objeto
        self.contenido_html = generar_html_desde_objeto(self)

    def save(self, *args, **kwargs):
        # --- Numeración ---
        # Solo calculamos el número si no existe (para evitar sobreescribir)
        if not self.numero:
            with transaction.atomic():  # Asegura que el cálculo sea atómico
                # Filtramos por plantilla + gestión + ambito (interno/externo)
                ultimo = CorrespondenciaElaborada.objects.filter(
                    gestion=self.gestion,
                    plantilla=self.plantilla,
                    ambito=self.ambito  # Se sigue diferenciando interno vs externo
                ).order_by('-numero').first()

                # Si hay un documento previo, sumamos 1; si no, comenzamos en 1
                self.numero = (ultimo.numero + 1) if ultimo else 1

        # --- Generación del CITE ---
        if not self.cite:
            if self.plantilla:
                sigla_tipo = self.plantilla.tipo.upper()  # Solo 'NOTA', 'COMUNICADO', etc.
            else:
                sigla_tipo = 'OTRO'

            # Agregamos un sufijo I/E según el ámbito
            ambito_sufijo = '-I' if self.ambito == 'interno' else '-E' if self.ambito == 'externo' else ''

            # Generamos el CITE completo
            # Ej: FSTL-FTA/NOTA-I/2025-001
            self.cite = f"{self.sigla}/{sigla_tipo}{ambito_sufijo}/{self.gestion}-{self.numero:03}"

        # --- Generar contenido HTML ---
        # Siempre se genera el HTML actualizado, incluso si ya existe uno
        self.generar_contenido_html()

        # --- Embedding semántico desde contenido_html ---
        # Solo recalcula si no existe o si el contenido cambió.
        if self.contenido_html:
            if self.pk:
                prev = CorrespondenciaElaborada.objects.filter(pk=self.pk).values_list(
                    "contenido_html", "vector_embedding_html"
                ).first()
                prev_html = prev[0] if prev else None
                prev_embedding = prev[1] if prev else None
                needs_update = (prev_embedding is None) or (prev_html != self.contenido_html)
            else:
                needs_update = True

            if needs_update:
                texto_plano = _build_semantic_text(self)
                if texto_plano:
                    modelo = _get_sbert_model()
                    self.vector_embedding_html = modelo.encode(texto_plano).tolist()

        # --- Guardar instancia ---
        super().save(*args, **kwargs)


class AccionCorrespondencia(models.Model):

    ACCIONES = [
        ('derivado', 'Derivado'),
        ('observado', 'Observado'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('devuelto', 'Devuelto'),
        ('archivado', 'Archivado'),
        #no coloco visto porque ya es campo en este modelo que cambia a true o false
    ]
    correspondencia = models.ForeignKey('Correspondencia', on_delete=models.CASCADE, related_name='acciones')
    usuario_origen = models.ForeignKey('usuario.CustomUser', on_delete=models.CASCADE, blank=True, null=True, related_name='acciones_origen')
    usuario_destino = models.ForeignKey('usuario.CustomUser', on_delete=models.CASCADE, blank=True, null=True, related_name='acciones_destino') #Es usuario destino
    accion = models.CharField(max_length=50, choices=ACCIONES)  # Derivar, Archivar, Rechazar, etc.
    comentario = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateTimeField(auto_now_add=True) #Cuando el documento fue registrado, derivado o creado
    fecha_modificacion = models.DateTimeField(auto_now=True)
    visto = models.BooleanField(default=False)
    fecha_visto = models.DateTimeField(null=True, blank=True)
    estado_resultante = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.accion.upper()} - {self.correspondencia} ({self.usuario_origen} → {self.usuario_destino})"

    def marcar_como_visto(self):
        if not self.visto:
            self.visto = True
            self.fecha_visto = timezone.now()
            self.save(update_fields=['visto', 'fecha_visto'])
            
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Primero guardamos la acción

        correspondencia = self.correspondencia

        # Sincroniza el estado general con la última acción relevante
        acciones_a_estado = {
            "aprobado": "aprobado",
            "rechazado": "rechazado",
            "archivado": "archivado",
            "devuelto": "devuelto",
            "derivado": "derivado",
            "observado": "observado",
        }

        nuevo_estado = acciones_a_estado.get(self.accion)
        if nuevo_estado:
            correspondencia.estado = nuevo_estado
            correspondencia.estado_actual = nuevo_estado.upper()
            correspondencia.save(update_fields=["estado", "estado_actual"])
