
from rest_framework import serializers
from .models import Documento, TipoDocumento
from correspondencia.models import Correspondencia

class DocumentoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Documento
        fields = '__all__'
        
class TipoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoDocumento
        fields = '__all__'
