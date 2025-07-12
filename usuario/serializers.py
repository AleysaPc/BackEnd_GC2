from rest_framework import serializers

from .models import * 
from django.contrib.auth import get_user_model 
User = get_user_model()

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'
class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = '__all__'

class LoginSerializer(serializers.Serializer):
    id=serializers.IntegerField(read_only=True)
    email = serializers.EmailField()
    password = serializers.CharField()
    

    name_rol = serializers.CharField(source="role.name", read_only=True)
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret.pop('password', None)
        return ret

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)
    name_rol = serializers.CharField(source="role.name", read_only=True)
    nombre_institucion = serializers.CharField(source="institucion.razon_social", read_only=True)
    nombre_departamento = serializers.CharField(source="departamento.nombre", read_only=True)
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'password',
            'new_password',
            'first_name',
            'secund_name',
            'last_name',
            'secund_last_name', 
            'is_superuser',
            'is_active',
            'date_joined',
            'birthday',
            'username',
            'role',  # Asegúrate de agregar 'role' aquí
            'name_rol',
            'institucion',
            'departamento',
            'nombre_institucion',
            'nombre_departamento',
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'new_password': {'write_only': True, 'required': False},  # 👈 Extra seguridad
        }

    def create(self, validated_data):
        if not validated_data.get('password'):
            raise serializers.ValidationError({'password': 'Este campo es requerido para crear un usuario.'})
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        new_password = validated_data.pop('new_password', None)
        if new_password:
            instance.set_password(new_password)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)  
        instance.save()
        return instance



