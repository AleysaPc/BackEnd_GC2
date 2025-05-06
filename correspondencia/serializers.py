from .models import Correspondencia, DocEntrante, DocSaliente, DocInterno
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

class DocEntranteSerializer(serializers.ModelSerializer):
    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)
    documentos = DocumentoSerializer(many=True)
    class Meta:
        model = DocEntrante
        fields = '__all__'               

    def create(self, validated_data):
        documentos_data = validated_data.pop('documentos')
        # Crea la correspondencia entrante
        doc_entrante = DocEntrante.objects.create(**validated_data)
        
        # Crea los documentos asociados
        for doc_data in documentos_data:
            Documento.objects.create(correspondencia=doc_entrante, **doc_data)
        
        return doc_entrante  # Retorna la correspondencia con los documentos creados

        
        return doc_entrante
class DocSalienteSerializer(serializers.ModelSerializer):

    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)

    class Meta:
        model = DocSaliente
        fields = '__all__'

class DocInternoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocInterno
        fields = '__all__'

        