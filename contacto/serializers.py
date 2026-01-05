from .models import Contacto, Institucion
from rest_framework import serializers


class InstitucionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institucion
        fields = '__all__'

class ContactoSerializer(serializers.ModelSerializer):  
    nombre_completo = serializers.SerializerMethodField()
    nombre_institucion = serializers.CharField(source='institucion.razon_social', read_only=True)   
    #Esto sale en el frontend
    class Meta:
        model = Contacto
        fields = '__all__'

  #Esto sale en el frontend.
    def get_nombre_completo(self, obj):
        return f"{obj.nombre_contacto} {obj.apellido_pat_contacto} {obj.apellido_mat_contacto} - {obj.titulo_profesional} "

# -------------------------------
# SELECTS
# -------------------------------
class InstitucionSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institucion
        fields = ['id_institucion', 'razon_social']