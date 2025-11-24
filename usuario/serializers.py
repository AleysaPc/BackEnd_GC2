from rest_framework import serializers

from .models import * 
from django.contrib.auth import get_user_model 
from contacto.models import Institucion

User = get_user_model()

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'content_type']

class GroupSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(queryset=Permission.objects.all(), many=True)
    #description = serializers.CharField(source="name")

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']

class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = '__all__'

class LoginSerializer(serializers.Serializer):
    id=serializers.IntegerField(read_only=True)
    email = serializers.EmailField()
    password = serializers.CharField()
    departamento = serializers.PrimaryKeyRelatedField(queryset=Departamento.objects.all(), source="departamento.id", required=False)
    full_name = serializers.SerializerMethodField()
    rol = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return obj.first_name + " " + obj.last_name

    def get_rol(self, obj):
        group = obj.groups.first()
        return group.name if group else None

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret.pop('password', None)
        return ret

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)
    nombre_departamento = serializers.CharField(source="departamento.nombre", read_only=True)
    nombre_institucion = serializers.CharField(source="institucion.razon_social", read_only=True)
    rol = serializers.SerializerMethodField()
    sigla = serializers.CharField(source="departamento.sigla", read_only=True)

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
            'departamento',
            'nombre_departamento',
            'sigla',
            'institucion',
            'nombre_institucion',
            'rol',
            'lugar_nacimiento',
            'documento_identidad',
            'direccion',
            'telefono',
            'celular',
            'cargo',
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'new_password': {'write_only': True, 'required': False},
        }

    def get_rol(self, obj):
        group = obj.groups.first()
        return group.name if group else None

    def create(self, validated_data):
        print("Datos recibidos en el serializer:")
        print(f"initial_data: {self.initial_data}")
        print(f"validated_data: {validated_data}")
        rol_id = self.initial_data.get("rol")
        # Buscar en ambos lugares: initial_data y validated_data
        institucion_id = self.initial_data.get("institucion") or validated_data.pop("institucion", None)
        password = validated_data.pop("password", None)
        
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        
        if institucion_id:
            try:
                institucion = Institucion.objects.get(id_institucion=institucion_id)
                user.institucion = institucion
            except (Institucion.DoesNotExist, ValueError):
                raise serializers.ValidationError({"institucion": "La institucion especificada no existe."})

        user.save()

        if rol_id:
            try:
                group = Group.objects.get(id=rol_id)
                user.groups.set([group])
            except Group.DoesNotExist:
                raise serializers.ValidationError({"rol": "El grupo especificado no existe."})

        return user


    def update(self, instance, validated_data):
        new_password = validated_data.pop('new_password', None)
        if new_password:
            instance.set_password(new_password)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)  
        instance.save()

        rol_id = self.initial_data.get("rol")
        if rol_id:
            try:
                group = Group.objects.get(id=rol_id)
                instance.groups.set([group])
            except Group.DoesNotExist:
                raise serializers.ValidationError({"rol": "El grupo especificado no existe."})

        return instance