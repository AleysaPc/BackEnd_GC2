from .models import Contacto, Institucion
from rest_framework import serializers


class InstitucionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institucion
        fields = '__all__'
class ContactoSerializer(serializers.ModelSerializer):  
    
    #Esto sale en el frontend.
    class Meta:
        model = Contacto
        fields = '__all__'