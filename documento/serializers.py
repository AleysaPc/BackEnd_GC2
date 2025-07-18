
from rest_framework import serializers
from .models import Documento
from correspondencia.models import Correspondencia
from documento.models import PlantillaDocumento

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
        
class PlantillaDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantillaDocumento
        fields = ['id_plantilla', 'nombre_plantilla', 'descripcion', 'estructura_html', 'tipo']
        read_only_fields = ['id_plantilla']
