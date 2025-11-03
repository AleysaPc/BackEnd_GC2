from rest_framework import serializers
from django.db import transaction
from django.core.files import File
from .models import Correspondencia, Recibida, Enviada, AccionCorrespondencia, CorrespondenciaElaborada, HistorialVisualizacion
from documento.models import Documento, PlantillaDocumento
from documento.serializers import DocumentoSerializer, PlantillaDocumentoSerializer
from usuario.models import CustomUser
from .utils import derivar_correspondencia


# ---------------------------
# Serializadores auxiliares
# ---------------------------
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email']


class AccionCorrespondenciaSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    usuario_destino = UsuarioSerializer(read_only=True)
    tipo = serializers.CharField(source='correspondencia.tipo', read_only=True)
    comentario_derivacion = serializers.CharField(write_only=True, required=False, allow_blank=True)
    usuario_destino_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source='usuario_destino',
        write_only=True,
        required=True
    )
    correspondencia_id = serializers.PrimaryKeyRelatedField(
        queryset=Recibida.objects.all(),
        source='correspondencia',
        write_only=True,
        required=True
    )

    class Meta:
        model = AccionCorrespondencia
        fields = [
            'id_accion', 'usuario', 'usuario_destino', 'usuario_destino_id',
            'accion', 'fecha', 'correspondencia_id', 'comentario_derivacion',
            'comentario', 'visto', 'tipo'
        ]

    def _handle_comentario_derivacion(self, validated_data):
        comentario = validated_data.pop('comentario_derivacion', None)
        if comentario is not None:
            validated_data['comentario'] = comentario
        return validated_data

    def create(self, validated_data):
        return super().create(self._handle_comentario_derivacion(validated_data))

    def update(self, instance, validated_data):
        return super().update(instance, self._handle_comentario_derivacion(validated_data))

# Listado y detalle general de correspondencias
class CorrespondenciaSerializer(serializers.ModelSerializer):
    documentos = DocumentoSerializer(many=True)
    contacto = serializers.StringRelatedField()
    acciones = AccionCorrespondenciaSerializer(many=True, read_only=True)

    class Meta:
        model = Correspondencia
        fields = [
            'id_correspondencia', 'tipo', 'descripcion', 'fecha_registro',
            'referencia', 'paginas', 'prioridad', 'estado',
            'documentos', 'contacto', 'usuario', 'acciones'
        ]
# ---------------------------
# Serializer base unificado
# ---------------------------
class CorrespondenciaSerializerBase(serializers.ModelSerializer):
    documentos = DocumentoSerializer(many=True, required=False)
    acciones = AccionCorrespondenciaSerializer(many=True, read_only=True)
    usuarios = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    comentario_derivacion = serializers.CharField(write_only=True, required=False, allow_blank=True)
    usuario = UsuarioSerializer(read_only=True)

    @staticmethod
    def _extraer_documentos(request):
        documentos_data = []
        if request and request.FILES:
            idx = 0
            while True:
                nombre = request.data.get(f'documentos[{idx}][nombre_documento]')
                archivo = request.FILES.get(f'documentos[{idx}][archivo]')
                if not nombre and not archivo:
                    break
                doc = {}
                if nombre:
                    doc['nombre_documento'] = nombre
                if archivo:
                    doc['archivo'] = archivo
                documentos_data.append(doc)
                idx += 1
        return documentos_data

    @staticmethod
    def _crear_documentos(correspondencia, documentos_data):
        for doc_data in documentos_data:
            if 'nombre_documento' in doc_data or 'archivo' in doc_data:
                if 'archivo' in doc_data and hasattr(doc_data['archivo'], 'temporary_file_path'):
                    doc_data['archivo'] = File(open(doc_data['archivo'].temporary_file_path(), 'rb'))
                Documento.objects.create(correspondencia=correspondencia, **doc_data)

    @transaction.atomic
    def _crear_o_actualizar(self, instance=None, validated_data=None):
        request = self.context.get('request')
        usuarios = validated_data.pop('usuarios', [])
        documentos_data = validated_data.pop('documentos', [])
        comentario_derivacion = validated_data.pop('comentario_derivacion', None)

        usuario_actual = getattr(request, 'user', None)
        if not usuario_actual or usuario_actual.is_anonymous:
            raise serializers.ValidationError("Usuario no autenticado")

        valid_users = [uid for uid in usuarios if CustomUser.objects.filter(id=uid).exists()]
        documentos_data += self._extraer_documentos(request)

        if instance is None:
            # Crear correspondencia
            if 'usuario' in self.Meta.model._meta.fields_map:
                validated_data['usuario'] = usuario_actual
            instance = self.Meta.model.objects.create(**validated_data)
        else:
            # Actualizar correspondencia
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

        # Crear/actualizar documentos
        if documentos_data:
            if instance.pk and instance.documentos.exists():
                instance.documentos.all().delete()
            self._crear_documentos(instance, documentos_data)

        # Derivar si hay usuarios destino
        if valid_users:
            derivar_correspondencia(
                correspondencia=instance,
                usuario_actual=usuario_actual,
                usuarios_destino=valid_users,
                comentario_derivacion=comentario_derivacion
            )

        return instance

    def create(self, validated_data):
        return self._crear_o_actualizar(validated_data=validated_data)

    def update(self, instance, validated_data):
        return self._crear_o_actualizar(instance=instance, validated_data=validated_data)


# ---------------------------
# Serializadores concretos
# ---------------------------
class RecibidaSerializer(CorrespondenciaSerializerBase):
    similitud = serializers.FloatField(read_only=True)
    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)

    class Meta:
        model = Recibida
        fields = [
            'id_correspondencia', 'tipo', 'descripcion', 'fecha_registro', 'fecha_recepcion', 'fecha_respuesta',
            'hora_recepcion', 'hora_respuesta', 'referencia', 'paginas', 'prioridad', 'estado',
            'documentos', 'contacto', 'usuario', 'acciones',
            'comentario_derivacion', 'usuarios', 'datos_contacto','similitud', 'nro_registro'
        ]


class EnviadaSerializer(CorrespondenciaSerializerBase):
    similitud = serializers.FloatField(read_only=True)
    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)

    class Meta:
        model = Enviada
        fields = [
            'id_correspondencia', 'tipo', 'descripcion', 'fecha_registro',
            'referencia', 'paginas', 'documentos', 'contacto', 'usuario', 'comentario',
            'acciones', 'datos_contacto', 'usuarios', 'fecha_envio', 'fecha_recepcion',
            'fecha_seguimiento', 'cite', 'similitud'
        ]


class CorrespondenciaElaboradaSerializer(CorrespondenciaSerializerBase):
    similitud = serializers.FloatField(read_only=True)
    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)
    nro_registro_respuesta = serializers.CharField(source='respuesta_a.nro_registro', read_only=True)
    documentos = DocumentoSerializer(many=True, read_only=True)
    acciones = AccionCorrespondenciaSerializer(many=True, read_only=True)
    plantilla = PlantillaDocumentoSerializer(read_only=True)
    plantilla_id = serializers.PrimaryKeyRelatedField(
        queryset=PlantillaDocumento.objects.all(),
        source='plantilla',
        write_only=False
    )

    class Meta:
        model = CorrespondenciaElaborada
        fields = [
            'id_correspondencia', 'fecha_envio', 'fecha_recepcion', 'fecha_seguimiento',
            'referencia', 'descripcion', 'prioridad', 'estado', 'contacto', 'usuario',
            'documentos', 'acciones', 'paginas', 'respuesta_a', 'datos_contacto', 'similitud',
            'plantilla', 'plantilla_id', 'sigla', 'numero', 'gestion', 'cite', 'firmado',
            'version', 'fecha_elaboracion', 'contenido_html', 'nro_registro_respuesta',
            'comentario_derivacion', 'usuarios', 'descripcion_introduccion',
            'descripcion_desarrollo', 'descripcion_conclusion'
        ]
        read_only_fields = ['numero', 'gestion', 'cite', 'contenido_html']


class HistorialVisualizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialVisualizacion
        fields = '__all__'
