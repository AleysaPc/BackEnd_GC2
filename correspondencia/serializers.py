from dataclasses import field
from rest_framework import serializers
from django.db import transaction
from django.core.files import File
from django.utils import timezone
from .models import Correspondencia, PreSelloRecibida, Recibida, Enviada, AccionCorrespondencia, CorrespondenciaElaborada
from documento.models import Documento, PlantillaDocumento
from documento.serializers import DocumentoSerializer, PlantillaDocumentoSerializer
from usuario.models import CustomUser
from usuario.serializers import CustomUserSerializer
from .utils import derivar_correspondencia


# ---------------------------
# Serializadores auxiliares
# ---------------------------
def _obtener_numero_documento(doc):
    if not doc:
        return None

    numero_directo = getattr(doc, "nro_registro", None) or getattr(doc, "cite", None)
    if numero_directo:
        return numero_directo

    doc_id = getattr(doc, "id_correspondencia", None)
    if not doc_id:
        return None

    nro_recibida = Recibida.objects.filter(
        id_correspondencia=doc_id
    ).values_list("nro_registro", flat=True).first()
    if nro_recibida:
        return nro_recibida

    cite_elaborada = CorrespondenciaElaborada.objects.filter(
        id_correspondencia=doc_id
    ).values_list("cite", flat=True).first()
    if cite_elaborada:
        return cite_elaborada

    cite_enviada = Enviada.objects.filter(
        id_correspondencia=doc_id
    ).values_list("cite", flat=True).first()
    if cite_enviada:
        return cite_enviada

    return None


class UsuarioSerializer(CustomUserSerializer):
    class Meta(CustomUserSerializer.Meta):
        fields = ['id', 'email', 'departamento', 'nombre_departamento', 'sigla','first_name', 'second_name', 'last_name', 'second_last_name']


class UsuarioMiniSerializer(serializers.ModelSerializer):
    nombre_departamento = serializers.CharField(source="departamento.nombre", read_only=True)
    sigla = serializers.CharField(source="departamento.sigla", read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'second_name', 'last_name', 'second_last_name', 'nombre_departamento', 'sigla']


class DocumentoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        fields = ['id_documento', 'nombre_documento']


class AccionCorrespondenciaSerializer(serializers.ModelSerializer):

    comentario_derivacion = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )

    #Usuarios Devuelve un objeto
    usuario_origen = UsuarioSerializer(read_only=True)
    usuario_destino = UsuarioSerializer(read_only=True) 

    #IDs que llegan desde el frontend
    usuario_origen_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source='usuario_origen',
        write_only=True,
        required=False
    )
    usuario_destino_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source='usuario_destino',
        required=True,
        write_only=True,
        many=True
    )   
    #Correspondencia Devuelve un objeto
    correspondencia_id = serializers.PrimaryKeyRelatedField(
        queryset=Correspondencia.objects.all(),
        write_only=True) #source=fuente
    
    #tipo = serializers.CharField(source='correspondencia.tipo', read_only=True)
    
    class Meta:
        model = AccionCorrespondencia
        fields = [
            'id', 'correspondencia','correspondencia_id','usuario_origen_id', 'usuario_destino_id', 'usuario_origen', 'usuario_destino',
            'accion','comentario_derivacion','comentario','fecha_inicio','fecha_modificacion','visto', 'fecha_visto','estado_resultante',
        ]
        read_only_fields = [
            'id',
            'fecha_inicio',
            'fecha_modificacion',
            'visto',
            'fecha_visto',
            'estado_resultante',
            'correspondencia',
            'usuario_origen',
            'usuario_destino',
            'es_en_respuesta',
        ]

    # coloca en el campo comentario, el comentario se guarda en el campo correcto sin afectar al serializador
    def _handle_comentario_derivacion(self, validated_data):
        comentario = validated_data.pop('comentario_derivacion', None)
        if comentario is not None:
            validated_data['comentario'] = comentario
        return validated_data

    #Crear nueva acción (registro de evento) request=pedido
    def create(self, validated_data):
        request = self.context.get('request')

        # usuario_origen = usuario logueado
        if request and request.user:
            validated_data['usuario_origen'] = request.user

        # comentario_derivacion → comentario
        validated_data = self._handle_comentario_derivacion(validated_data)

        # lista de usuarios destino
        usuarios_destino = validated_data.pop('usuario_destino')

        # obtener correspondencia_id y convertir en objeto Correspondencia
        correspondencia = validated_data.pop('correspondencia_id')

        acciones_creadas = []

        for usuario in usuarios_destino:
            data = validated_data.copy()
            data['usuario_destino'] = usuario
            data['correspondencia'] = correspondencia  # <--- asignar objeto correcto
            accion = AccionCorrespondencia.objects.create(**data)
            acciones_creadas.append(accion)
    

        return acciones_creadas[0]

    #Actualizar acción (por ejemplo, marcar como vista)
    def update(self, instance, validated_data):
        validated_data = self._handle_comentario_derivacion(validated_data)
        
        #Si pasa de no visto a visto, registrar fecha_visto
        if 'visto' in validated_data and validated_data['visto'] and not instance.visto:
            validated_data['fecha_visto'] = timezone.now()

        return super().update(instance, validated_data)


class AccionCorrespondenciaListSerializer(serializers.ModelSerializer):
    usuario_origen = UsuarioMiniSerializer(read_only=True)
    usuario_destino = UsuarioMiniSerializer(read_only=True)

    class Meta:
        model = AccionCorrespondencia
        fields = [
            'id', 'accion', 'comentario', 'fecha_inicio', 'visto', 'fecha_visto',
            'estado_resultante', 'usuario_origen', 'usuario_destino',
        ]


# Listado y detalle general de correspondencias
class CorrespondenciaSerializer(serializers.ModelSerializer):
    documentos = DocumentoSerializer(many=True)
    contacto = serializers.StringRelatedField()
    acciones = AccionCorrespondenciaSerializer(many=True, read_only=True)
    usuario = UsuarioSerializer(read_only=True)

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
    usuarios = serializers.ListField(child=serializers.IntegerField(), write_only=False, required=False)
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

        usuario = getattr(request, 'user', None)
        if not usuario or usuario.is_anonymous:
            raise serializers.ValidationError("Usuario no autenticado")

        valid_users = [uid for uid in usuarios if CustomUser.objects.filter(id=uid).exists()]
        documentos_data += self._extraer_documentos(request)

        if instance is None:
            # Crear correspondencia
            if 'usuario' in self.Meta.model._meta.fields_map:
                validated_data['usuario'] = usuario
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

        # Derivar correspondencia solo si no está en borrador
        if instance.estado != 'borrador':
            if not valid_users:
                raise serializers.ValidationError(
                    "Debe especificar al menos un suaurio destino"
                )
            derivar_correspondencia(
                correspondencia=instance,
                usuario_origen=usuario,
                usuario_destino=valid_users,
                comentario_derivacion=comentario_derivacion
            )

        return instance

    def create(self, validated_data):
        return self._crear_o_actualizar(validated_data=validated_data)

    def update(self, instance, validated_data):
        return self._crear_o_actualizar(instance=instance, validated_data=validated_data)


class RespuestaRelacionSerializer(serializers.ModelSerializer):
    acciones = AccionCorrespondenciaSerializer(many=True, read_only=True)
    respuestas = serializers.SerializerMethodField()
    numero_documento = serializers.SerializerMethodField()

    class Meta:
        model = CorrespondenciaElaborada
        fields = [
            "id_correspondencia",
            "referencia",
            "estado",
            "fecha_registro",
            "cite",
            "numero_documento",
            "acciones",
            "respuestas",
        ]

    def get_numero_documento(self, obj):
        return getattr(obj, "cite", None)

    def get_respuestas(self, obj):
        hijos = CorrespondenciaElaborada.objects.filter(
            respuesta_a=obj,
        ).order_by("fecha_registro")
        return RespuestaRelacionSerializer(hijos, many=True, context=self.context).data


# ---------------------------
# Serializadores concretos
# ---------------------------
class RecibidaSerializer(CorrespondenciaSerializerBase):
    similitud = serializers.FloatField(read_only=True)
    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)
    respuestas = serializers.SerializerMethodField()
    relacionada_a_info = serializers.SerializerMethodField()

    class Meta:
        model = Recibida
        fields = [
            'id_correspondencia', 'tipo', 'descripcion', 'fecha_registro', 'fecha_recepcion', 'fecha_respuesta',
            'referencia', 'paginas', 'prioridad', 'estado',
            'documentos', 'contacto', 'usuario', 'acciones',
            'comentario_derivacion', 'usuarios', 'datos_contacto','similitud', 'nro_registro',
            'respuestas', 'relacionada_a', 'relacionada_a_info',
        ]
        extra_kwargs = {
            'fecha_recepcion': {'required': False},
        }

    def get_respuestas(self, obj):
        respuestas = CorrespondenciaElaborada.objects.filter(
            respuesta_a=obj,
        ).order_by("fecha_registro")
        return RespuestaRelacionSerializer(respuestas, many=True, context=self.context).data

    def get_relacionada_a_info(self, obj):
        parent = getattr(obj, "relacionada_a", None)
        if not parent:
            return None
        return {
            "id_correspondencia": parent.id_correspondencia,
            "tipo": parent.tipo,
            "referencia": parent.referencia,
            "numero": _obtener_numero_documento(parent),
        }


class RecibidaListSerializer(serializers.ModelSerializer):
    contacto = serializers.StringRelatedField()
    usuario = UsuarioMiniSerializer(read_only=True)
    documentos = DocumentoListSerializer(many=True, read_only=True)
    acciones = AccionCorrespondenciaListSerializer(many=True, read_only=True)
    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)

    class Meta:
        model = Recibida
        fields = [
            'id_correspondencia', 'tipo', 'referencia', 'fecha_registro', 'fecha_recepcion',
            'prioridad', 'estado', 'nro_registro', 'contacto', 'datos_contacto',
            'usuario', 'documentos', 'acciones',
        ]


class PreSelloSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreSelloRecibida
        fields = '__all__'


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


class EnviadaListSerializer(serializers.ModelSerializer):
    contacto = serializers.StringRelatedField()
    usuario = UsuarioMiniSerializer(read_only=True)
    documentos = DocumentoListSerializer(many=True, read_only=True)
    acciones = AccionCorrespondenciaListSerializer(many=True, read_only=True)
    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)

    class Meta:
        model = Enviada
        fields = [
            'id_correspondencia', 'tipo', 'referencia', 'fecha_registro', 'prioridad',
            'estado', 'cite', 'fecha_envio', 'fecha_recepcion', 'fecha_seguimiento',
            'contacto', 'datos_contacto', 'usuario', 'documentos', 'acciones',
        ]


class CorrespondenciaElaboradaSerializer(CorrespondenciaSerializerBase):
    similitud = serializers.FloatField(read_only=True)
    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)
    nro_registro_respuesta = serializers.SerializerMethodField()
    documentos = DocumentoSerializer(many=True, read_only=True)
    acciones = AccionCorrespondenciaSerializer(many=True, read_only=True)
    plantilla = PlantillaDocumentoSerializer(read_only=True)
    plantilla_id = serializers.PrimaryKeyRelatedField(
        queryset=PlantillaDocumento.objects.all(),
        source='plantilla',
        write_only=False
    )
    destino_interno_info = UsuarioSerializer(source='destino_interno', read_only=True)
    destino_interno = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
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
            'descripcion_desarrollo', 'descripcion_conclusion','ambito', 'destino_interno', 'destino_interno_info', 'tipo',
        ]
        read_only_fields = ['numero', 'gestion', 'cite', 'contenido_html']
        extra_kwargs = {
            'tipo': {'required': False},
        }

    def get_nro_registro_respuesta(self, obj):
        parent = getattr(obj, "respuesta_a", None)
        if not parent:
            return None
        return _obtener_numero_documento(parent)

    def create(self, validated_data):
        if not validated_data.get('usuario'):
            # Asignar automáticamente el usuario que hace la petición
            validated_data['usuario'] = self.context['request'].user
        if not validated_data.get('tipo'):
            validated_data['tipo'] = 'enviado'
        return super().create(validated_data)


class CorrespondenciaElaboradaListSerializer(serializers.ModelSerializer):
    contacto = serializers.StringRelatedField()
    usuario = UsuarioMiniSerializer(read_only=True)
    documentos = DocumentoListSerializer(many=True, read_only=True)
    acciones = AccionCorrespondenciaListSerializer(many=True, read_only=True)
    plantilla = PlantillaDocumentoSerializer(read_only=True)
    destino_interno_info = UsuarioMiniSerializer(source='destino_interno', read_only=True)
    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)

    class Meta:
        model = CorrespondenciaElaborada
        fields = [
            'id_correspondencia', 'tipo', 'referencia', 'fecha_registro', 'prioridad',
            'estado', 'cite', 'ambito', 'firmado', 'version', 'fecha_elaboracion',
            'fecha_envio', 'fecha_recepcion', 'fecha_seguimiento',
            'contacto', 'datos_contacto', 'usuario', 'plantilla', 'destino_interno_info',
            'documentos', 'acciones',
        ]

