from .models import Correspondencia, Recibida, Enviada, Interna
from rest_framework import serializers
from documento.serializers import DocumentoSerializer
from contacto.serializers import ContactoSerializer 
from documento.models import Documento

class CorrespondenciaListSerializer(serializers.ModelSerializer):
    documentos = DocumentoSerializer(many=True)
    contacto = serializers.StringRelatedField()
    
    class Meta: 
            model = Correspondencia
            fields = [
                'id_correspondencia',
                'tipo',
                'descripcion', #Descripción esta si aparece en la creación del frontend
                'fecha_registro',
                'referencia',
                'paginas',
                'prioridad',
                'estado',
                'documentos',
                'contacto', #Unicamente necesitamos el ID para el registro en el frontend
                'usuario', #Usuario que crea la correspondencia
                'comentario',
                #'usuario', #Usuario que crea la correspondencia
                
            ]

class CorrespondenciaDetailSerializer(serializers.ModelSerializer):
    documentos = DocumentoSerializer(many=True, read_only=True, required=False)
    contacto = serializers.StringRelatedField()
    
    class Meta: 
            model = Correspondencia
            fields = [
                'id_correspondencia',
                'tipo',
                'descripcion', #Descripción esta si aparece en la creación del frontend
                'fecha_registro',
                'referencia',
                'paginas',
                'prioridad',
                'estado',
                'documentos',
                'contacto', #Unicamente necesitamos el ID para el registro en el frontend
                'usuario', #Usuario que crea la correspondencia
                'comentario',
                #'usuario', #Usuario que crea la correspondencia
                
            ]

class RecibidaSerializer(serializers.ModelSerializer):
    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)
    documentos = DocumentoSerializer(many=True, required=False)

    class Meta:
        model = Recibida
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')

        # ⚠️ Saca los documentos antes de pasar validated_data al modelo
        documentos_data = []
        if request and request.method.lower() == 'post':
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
        else:
            # También puede venir del validador por JSON si no es multipart
            documentos_data = validated_data.pop('documentos', [])

        # 🔥 Aquí eliminamos el campo 'documentos' del validated_data
        validated_data.pop('documentos', None)

        # ✅ Creamos la instancia principal
        doc_entrante = Recibida.objects.create(**validated_data)

        # ✅ Creamos los documentos relacionados
        for doc_data in documentos_data:
            Documento.objects.create(correspondencia=doc_entrante, **doc_data)

        return doc_entrante



class EnviadaSerializer(serializers.ModelSerializer):

    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)

    class Meta:
        model = Enviada
        fields = '__all__'

class InternaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interna
        fields = '__all__'

        