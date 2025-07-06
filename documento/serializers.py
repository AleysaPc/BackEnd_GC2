
from rest_framework import serializers
from .models import Documento
from correspondencia.models import Correspondencia

class DocumentoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Documento
        fields = '__all__'
        
