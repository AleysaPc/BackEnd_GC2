
from rest_framework import serializers
from .models import Documento
from correspondencia.models import Correspondencia

class DocumentoSerializer(serializers.ModelSerializer):
    
    # el campo correspondencia no es requerido en la petición (porque el backend se encargará):
    class Meta:
        model = Documento
        fields = '__all__'
        extra_kwargs = {
            'correspondencia': {'required': False},
            'archivo': {'required': False}, #no sirve poner
            'nombre_archivo': {'required': False},
        }
        
