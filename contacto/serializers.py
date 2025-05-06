from .models import Contacto, Institucion
from rest_framework import serializers


class InstitucionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institucion
        fields = '__all__'
class ContactoSerializer(serializers.ModelSerializer):  
    institucion = InstitucionSerializer()
    nombre_completo = serializers.SerializerMethodField()
    #Esto sale en el frontend
    class Meta:
        model = Contacto
        fields = '__all__'

  #Esto sale en el frontend.
    def get_nombre_completo(self, obj):
        return f"{obj.nombre_contacto} {obj.apellido_pat_contacto} {obj.apellido_mat_contacto} - {obj.titulo_profesional} - {obj.institucion.razon_social}"