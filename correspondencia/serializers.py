from rest_framework import serializers
from .models import Correspondencia, Recibida, Enviada, AccionCorrespondencia, CorrespondenciaElaborada
from documento.serializers import DocumentoSerializer, PlantillaDocumentoSerializer
from contacto.serializers import ContactoSerializer
from documento.models import Documento, PlantillaDocumento
from usuario.models import CustomUser
from .utils import derivar_correspondencia
from django.db import transaction
from rest_framework import serializers


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email']  # Solo los campos que quieras mostrar

# Serializador para AccionCorrespondencia
class AccionCorrespondenciaSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    usuario_destino = UsuarioSerializer(read_only=True)

    comentario_derivacion = serializers.CharField(write_only=True, required=False)

    usuario_destino_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source='usuario_destino',
        write_only=True,
        required=True
    )

    # ✅ Campo corregido: ahora se puede escribir correspondencia_id
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
            'comentario'
        ]

    def create(self, validated_data):
        comentario_derivacion = validated_data.pop('comentario_derivacion', None)
        if comentario_derivacion is not None:
            validated_data['comentario'] = comentario_derivacion
        return super().create(validated_data)

    def update(self, instance, validated_data):
        comentario_derivacion = validated_data.pop('comentario_derivacion', None)
        if comentario_derivacion is not None:
            validated_data['comentario'] = comentario_derivacion
        return super().update(instance, validated_data)

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

# Recibida con opción de derivación múltiple
class RecibidaSerializer(serializers.ModelSerializer):
    similitud = serializers.FloatField(read_only=True)
    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)
    documentos = DocumentoSerializer(many=True, required=False)
    acciones = AccionCorrespondenciaSerializer(many=True, read_only=True)
    comentario_derivacion = serializers.CharField(write_only=True, required=False)
    usuarios = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    usuario = UsuarioSerializer(read_only=True) #Para poder obtener los datos del usuario que registro el documento

    class Meta:
        model = Recibida
        fields = [
            'id_correspondencia', 'tipo', 'descripcion', 'fecha_registro', 'fecha_recepcion', 'fecha_respuesta', 'hora_recepcion', 'hora_respuesta',
            'referencia', 'paginas', 'prioridad', 'estado',
            'documentos', 'contacto', 'usuario', 'acciones',
            'comentario_derivacion', 'usuarios', 'datos_contacto','similitud', 'nro_registro'
        ]
    
    @transaction.atomic  # Asegura que toda la creación sea atómica
    def create(self, validated_data):
        request = self.context.get('request')
        usuarios = validated_data.pop('usuarios', [])
        documentos_data = validated_data.pop('documentos', [])
        comentario_derivacion = validated_data.pop('comentario_derivacion', None)  # Extract here
 
        # Validar que haya un usuario autenticado
        usuario_actual = getattr(request, 'user', None)
        if usuario_actual is None or usuario_actual.is_anonymous:
            raise serializers.ValidationError("Usuario no autenticado")

        # Validar que los IDs de usuarios existan en la BD
        valid_users = [
            uid for uid in usuarios if CustomUser.objects.filter(id=uid).exists()
        ]

        # Leer documentos desde archivos multipart (si vienen así)
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

        # Crear la correspondencia con campos simples (sin comentario_derivacion)
        doc_entrante = Recibida.objects.create(
            usuario=usuario_actual,  # Asigna el usuario autenticado
            **validated_data
        )

        # Crear documentos relacionados
        for doc_data in documentos_data:
            # Opcional: validar que archivo y nombre no estén vacíos
            if 'nombre_documento' in doc_data or 'archivo' in doc_data:
                Documento.objects.create(correspondencia=doc_entrante, **doc_data)

        #usar función para derivar
        derivar_correspondencia(
            correspondencia=doc_entrante,
            usuario_actual=usuario_actual,
            usuarios_destino=valid_users,
            comentario_derivacion=comentario_derivacion
        )
        
        return doc_entrante
    
    @transaction.atomic  # Asegura que la actualización sea atómica
    def update(self, instance, validated_data):
        print(" Ejecutando UPDATE del serializer...")

        request = self.context.get('request')
        documentos_data = validated_data.pop('documentos', None)
        usuarios_data = validated_data.pop('usuarios', None)

        # Validar usuario autenticado
        usuario_actual = getattr(request, 'user', None)
        if usuario_actual is None or usuario_actual.is_anonymous:
            raise serializers.ValidationError("Usuario no autenticado")

        print(" validated_data (campos simples):", validated_data)
        print(" documentos_data:", documentos_data)
        print(" usuarios_data:", usuarios_data)

        # Actualizar campos simples del objeto Recibida
        for attr, value in validated_data.items():
            print(f" Actualizando campo: {attr} = {value}")
            setattr(instance, attr, value)
        instance.save()

        # Leer nuevos documentos enviados por multipart/form-data
        if request and request.method.lower() in ['put', 'patch'] and request.FILES:
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

        # Agregar nuevos documentos (sin eliminar los existentes)
        if documentos_data:
            print(" Agregando nuevos documentos...")
            for doc_data in documentos_data:
                if 'nombre_documento' in doc_data or 'archivo' in doc_data:
                    print(" Documento nuevo:", doc_data)
                    Documento.objects.create(correspondencia=instance, **doc_data)

        #Actualizar derivaciones usando función ubicada en utils.py
        if usuarios_data is not None:
            derivar_correspondencia(
                correspondencia=instance,
                usuario_actual=usuario_actual,
                usuarios_destino=usuarios_data,
                comentario_derivacion=validated_data.get('comentario_derivacion')  # uso correcto
            )

        return instance
  


# Enviada con opción de derivación múltiple (igual que Recibida)
class EnviadaSerializer(serializers.ModelSerializer):
    similitud = serializers.FloatField(read_only=True)
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
            'datos_contacto', 'usuarios', 'fecha_envio', 'fecha_recepcion', 'fecha_seguimiento', 'cite', 'similitud'
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
                accion="DERIVADO"
            )

        return doc_enviada

    def update(self, instance, validated_data):
        request = self.context.get('request')
        documentos_data = validated_data.pop('documentos', None)
        usuarios = validated_data.pop('usuarios', None)

        # Actualizar los campos simples del modelo Enviada
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

    # Actualizar documentos asociados
        if documentos_data is not None:
            # Elimina los documentos anteriores asociados a esta correspondencia
            instance.documentos.all().delete()

            # Si vienen documentos por multipart/form-data
            if request and request.FILES:
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

        # Crear nuevos documentos
        for doc_data in documentos_data:
            Documento.objects.create(correspondencia=instance, **doc_data)

    # Actualizar las derivaciones (acciones de correspondencia)
        if usuarios is not None:
            # Eliminar acciones anteriores
            instance.acciones.all().delete()

            # Crear nuevas acciones de derivación
            for usuario_id in usuarios:
                if CustomUser.objects.filter(id=usuario_id).exists():
                    AccionCorrespondencia.objects.create(
                        correspondencia=instance,
                        usuario_id=usuario_id,
                        accion="DERIVADO"
                    )

        return instance


# Documento Elaborado
class CorrespondenciaElaboradaSerializer(serializers.ModelSerializer):
    similitud = serializers.FloatField(read_only=True)
    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)
    nro_registro_respuesta = serializers.CharField(source='respuesta_a.nro_registro', read_only=True)
    documentos = DocumentoSerializer(many=True, read_only=True)
    acciones = AccionCorrespondenciaSerializer(many=True, read_only=True)
    comentario_derivacion = serializers.CharField(write_only=True, required=False, allow_blank=True) #allow_blank=True indica al validador que no rechace una cadena vacía fue la solución para que comentario deivación no sea obligatorio. 
    usuarios = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    plantilla = PlantillaDocumentoSerializer(read_only=True)
    plantilla_id = serializers.PrimaryKeyRelatedField(
        queryset=PlantillaDocumento.objects.all(),
        source='plantilla',
        write_only=False
    )

    class Meta:
        model = CorrespondenciaElaborada
        fields = [
            'id_correspondencia',
            'fecha_envio',
            'fecha_recepcion',
            'fecha_seguimiento',
            'referencia',
            'descripcion',
            'prioridad',
            'estado',
            'contacto',
            'usuario',
            'documentos',
            'acciones',
            'paginas',
            'respuesta_a',
            'datos_contacto',
            'similitud',
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
            'nro_registro_respuesta',
            'comentario_derivacion',
            'usuarios',
        ]
        read_only_fields = ['numero', 'gestion', 'cite', 'contenido_html', 'usuario',]

    
    def _leer_documentos_desde_request(self, request):
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
        return documentos_data

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        usuarios = validated_data.pop('usuarios', [])
        comentario_derivacion = validated_data.pop('comentario_derivacion', None)

        documentos_data = self._leer_documentos_desde_request(request)

        # Crear la correspondencia
        doc_elaborado = CorrespondenciaElaborada.objects.create(**validated_data)

        # Asociar documentos
        for doc_data in documentos_data:
            Documento.objects.create(correspondencia=doc_elaborado, **doc_data)

        # Derivar si hay usuarios destino
        if usuarios:
            valid_users = [uid for uid in usuarios if CustomUser.objects.filter(id=uid).exists()]
            derivar_correspondencia(
                correspondencia=doc_elaborado,
                usuario_actual=request.user,
                usuarios_destino=valid_users,
                comentario_derivacion=comentario_derivacion
            )

        return doc_elaborado

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get('request')
        usuarios = validated_data.pop('usuarios', [])
        comentario_derivacion = validated_data.pop('comentario_derivacion', None)  # ✅ sacamos antes

        # Actualizar campos simples
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Eliminar documentos existentes si quieres reemplazarlos
        instance.documentos.all().delete()

        documentos_data = self._leer_documentos_desde_request(request)

        # Asociar nuevos documentos
        for doc_data in documentos_data:
            Documento.objects.create(correspondencia=instance, **doc_data)

        # Derivar si hay cambios
        if usuarios:
            valid_users = [uid for uid in usuarios if CustomUser.objects.filter(id=uid).exists()]
            derivar_correspondencia(
                correspondencia=instance,
                usuario_actual=request.user,
                usuarios_destino=valid_users,
                comentario_derivacion=comentario_derivacion  # ✅ ahora seguro existe
            )

        return instance
