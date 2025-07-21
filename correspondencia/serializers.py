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
    
    def update(self, instance, validated_data):
        print("🟡 Ejecutando UPDATE del serializer...")
    
        request = self.context.get('request')
        documentos_data = validated_data.pop('documentos', None)
        usuarios_data = validated_data.pop('usuarios', None)
    
        print("✅ validated_data (campos simples):", validated_data)
        print("📄 documentos_data:", documentos_data)
        print("👤 usuarios_data:", usuarios_data)
    
        # Actualizar campos simples de la correspondencia
        for attr, value in validated_data.items():
            print(f"🔄 Actualizando campo: {attr} = {value}")
            setattr(instance, attr, value)
        instance.save()
    
        # Si vienen archivos desde el frontend en formato multipart
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
    
        # Agregar nuevos documentos, sin borrar los anteriores
        if documentos_data:
            print("📥 Agregando nuevos documentos...")
            for doc_data in documentos_data:
                print("📄 Documento nuevo:", doc_data)
                Documento.objects.create(correspondencia=instance, **doc_data)
    
        # Manejo de usuarios si fuera necesario
        if usuarios_data is not None:
            print("👤 Manejo de usuarios aún no implementado")
    
        print("✅ UPDATE completo")
        return instance
  

# 🔹 Enviada con opción de derivación múltiple (igual que Recibida)
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
                accion="DERIVAR"
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

    # 📝 Actualizar documentos asociados
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

    # 🔁 Actualizar las derivaciones (acciones de correspondencia)
        if usuarios is not None:
            # Eliminar acciones anteriores
            instance.acciones.all().delete()

            # Crear nuevas acciones de derivación
            for usuario_id in usuarios:
                if CustomUser.objects.filter(id=usuario_id).exists():
                    AccionCorrespondencia.objects.create(
                        correspondencia=instance,
                        usuario_id=usuario_id,
                        accion="DERIVAR"
                    )

        return instance


# 🔹 Documento Elaborado
class CorrespondenciaElaboradaSerializer(serializers.ModelSerializer):
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
            'id_correspondencia',
            'fecha_envio',
            'fecha_recepcion',
            'fecha_seguimiento',
            'referencia',
            'descripcion',
            'prioridad',
            'estado',
            'comentario',
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
        ]
        read_only_fields = ['numero', 'gestion', 'cite', 'contenido_html', 'usuario',]
    def update(self, instance, validated_data):
        request = self.context.get('request')
        documentos_data = validated_data.pop('documentos', None)
        plantilla = validated_data.pop('plantilla', None)

    # Actualizar campos simples
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if plantilla:
            instance.plantilla = plantilla
        instance.save()

    # Actualizar documentos (si se enviaron)
        if documentos_data is not None:
        # Eliminar documentos anteriores
            instance.documentos.all().delete()

        # Leer documentos desde multipart
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

        return instance

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
        doc_entrante = CorrespondenciaElaborada.objects.create(**validated_data)

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

