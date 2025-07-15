from rest_framework import serializers
from .models import Correspondencia, Recibida, Enviada, AccionCorrespondencia, CorrespondenciaElaborada
from documento.serializers import DocumentoSerializer, PlantillaDocumentoSerializer
from contacto.serializers import ContactoSerializer
from documento.models import Documento, PlantillaDocumento
from usuario.models import CustomUser

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email']  # Solo los campos que quieras mostrar

# 🔹 Mostrar ID del usuario al derivar
class AccionCorrespondenciaSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)  # ← esto es clave

    class Meta:
        model = AccionCorrespondencia
        fields = ['id_accion', 'usuario', 'accion', 'fecha']

# 🔹 Listado y detalle general de correspondencias
class CorrespondenciaListSerializer(serializers.ModelSerializer):
    documentos = DocumentoSerializer(many=True)
    contacto = serializers.StringRelatedField()
    acciones = AccionCorrespondenciaSerializer(many=True, read_only=True)

    class Meta:
        model = Correspondencia
        fields = [
            'id_correspondencia', 'tipo', 'descripcion', 'fecha_registro',
            'referencia', 'paginas', 'prioridad', 'estado',
            'documentos', 'contacto', 'usuario', 'comentario', 'acciones'
        ]


class CorrespondenciaDetailSerializer(serializers.ModelSerializer):
    documentos = DocumentoSerializer(many=True, read_only=True)
    contacto = serializers.StringRelatedField()
    acciones = AccionCorrespondenciaSerializer(many=True, read_only=True)

    class Meta:
        model = Correspondencia
        fields = [
            'id_correspondencia', 'tipo', 'descripcion', 'fecha_registro',
            'referencia', 'paginas', 'prioridad', 'estado',
            'documentos', 'contacto', 'usuario', 'comentario', 'acciones'
        ]


# 🔹 Recibida con opción de derivación múltiple
class RecibidaSerializer(serializers.ModelSerializer):
    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)
    documentos = DocumentoSerializer(many=True, required=False)
    acciones = AccionCorrespondenciaSerializer(many=True, read_only=True)
    usuarios = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Recibida
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')
        usuarios = validated_data.pop('usuarios', [])
        documentos_data = validated_data.pop('documentos', [])

        valid_users = [
            uid for uid in usuarios if CustomUser.objects.filter(id=uid).exists()
        ]

        # Leer archivos si se envían desde multipart (como desde el frontend)
        if request and request.method.lower() == 'post' and request.FILES:
            documentos_data = []
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

        # Crear la correspondencia
        doc_entrante = Recibida.objects.create(**validated_data)

        # Asociar documentos
        for doc_data in documentos_data:
            Documento.objects.create(correspondencia=doc_entrante, **doc_data)

        # Derivar a múltiples usuarios
        for usuario_id in valid_users:
            AccionCorrespondencia.objects.create(
                correspondencia=doc_entrante,
                usuario_id=usuario_id,
                accion="DERIVAR"
            )

        return doc_entrante


# 🔹 Enviada con opción de derivación múltiple (igual que Recibida)
class EnviadaSerializer(serializers.ModelSerializer):
    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)
    documentos = DocumentoSerializer(many=True, required=False)
    acciones = AccionCorrespondenciaSerializer(many=True, read_only=True)
    usuarios = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Enviada
        fields = [
            'id_correspondencia', 'tipo', 'descripcion', 'fecha_registro',
            'referencia', 'paginas',
            'documentos', 'contacto', 'usuario', 'comentario', 'acciones',
            'datos_contacto', 'usuarios', 'fecha_envio', 'fecha_recepcion', 'fecha_seguimiento', 'cite'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        usuarios = validated_data.pop('usuarios', [])
        documentos_data = validated_data.pop('documentos', [])

        valid_users = [
            uid for uid in usuarios if CustomUser.objects.filter(id=uid).exists()
        ]

        # Leer archivos si se envían desde multipart (como desde el frontend)
        if request and request.method.lower() == 'post' and request.FILES:
            documentos_data = []
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

        # Crear la correspondencia
        doc_enviada = Enviada.objects.create(**validated_data)

        # Asociar documentos
        for doc_data in documentos_data:
            Documento.objects.create(correspondencia=doc_enviada, **doc_data)

        # Derivar a múltiples usuarios
        for usuario_id in valid_users:
            AccionCorrespondencia.objects.create(
                correspondencia=doc_enviada,
                usuario_id=usuario_id,
                accion="DERIVAR"
            )

        return doc_enviada


# 🔹 Documento Elaborado
class CorrespondenciaElaboradaSerializer(serializers.ModelSerializer):
    plantilla = PlantillaDocumentoSerializer(read_only=True)
    plantilla_id = serializers.PrimaryKeyRelatedField(
        queryset=PlantillaDocumento.objects.all(),
        source='plantilla',
        write_only=True
    )

    class Meta:
        model = CorrespondenciaElaborada
        fields = [
            'id_correspondencia',
            'referencia',
            'descripcion',
            'prioridad',
            'estado',
            'comentario',
            'contacto',
            'usuario',

            'plantilla',       # representación anidada solo lectura
            'plantilla_id',    # para enviar id al crear/actualizar
            'sigla',
            'numero',
            'gestion',
            'cite',
            'firmado',
            'version',
            'fecha_elaboracion',
            'contenido_html',
            'usuario',
            
        ]
        read_only_fields = ['numero', 'gestion', 'cite', 'contenido_html', 'usuario',]

    def create(self, validated_data):
        instancia = CorrespondenciaElaborada.objects.create(**validated_data)
        return instancia


    def update(self, instance, validated_data):
        plantilla = validated_data.pop('plantilla', None)
        if plantilla:
            instance.plantilla = plantilla
        return super().update(instance, validated_data)