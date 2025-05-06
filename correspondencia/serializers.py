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
    
    documentos = DocumentoSerializer(many=True) 
    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)
    class Meta:
        model = DocEntrante
        fields = '__all__'               

class DocSalienteSerializer(serializers.ModelSerializer):

    datos_contacto = serializers.StringRelatedField(source='contacto', read_only=True)

    class Meta:
        model = DocSaliente
        fields = '__all__'

class DocInternoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocInterno
        fields = '__all__'

        