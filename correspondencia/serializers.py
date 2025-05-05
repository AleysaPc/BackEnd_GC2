from .models import Correspondencia, DocEntrante, DocSaliente, DocInterno
from rest_framework import serializers
from documento.serializers import DocumentoSerializer
from contacto.serializers import ContactoSerializer 

class CorrespondenciaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Correspondencia
        fields = '__all__'

class CorrespondenciaDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Correspondencia
        fields = '__all__'

class DocEntranteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocEntrante
        fields = '__all__'

class DocSalienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocSaliente
        fields = '__all__'

class DocInternoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocInterno
        fields = '__all__'

        