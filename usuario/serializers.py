from rest_framework import serializers #si
from .models import * #si
from django.contrib.auth import get_user_model #si
from contacto.models import Institucion #no
import re
from django.contrib.auth.models import Group
from django.db import transaction

User = get_user_model() #Obtiene el modelo del usuario 

class PermissionSerializer(serializers.ModelSerializer): #serializador para el modelo de permiso
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'content_type']

class RolSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(queryset=Permission.objects.all(), many=True)

    class Meta:
        model = Group
        fields =  ['id', 'name', 'permissions']


class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = '__all__' #Nolo tiene definido

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
        return [group.name for group in obj.groups.all()]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret.pop('password', None)
        return ret

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)
    nombre_departamento = serializers.CharField(source="departamento.nombre", read_only=True)
    nombre_institucion = serializers.CharField(source="institucion.razon_social", read_only=True)
    roles = serializers.SerializerMethodField()
    sigla = serializers.CharField(source="departamento.sigla", read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'password',
            'new_password',
            'first_name',
            'second_name',
            'last_name',
            'second_last_name', 
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
            'roles',
            'lugar_nacimiento',
            'documento_identidad',
            'direccion',
            'telefono',
            'celular',
            'cargo',
            'imagen',
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'new_password': {'write_only': True, 'required': False},
        }
    
    #Validaciones
    def validate_email(self, value):
        #Verifica si o tro usuario ya tiene ese email
        user = self.instance
        if User.objects.filter(email=value).exclude(id=getattr(user,'id', None)).exists():
            raise serializers.ValidationError("Este correo electrónico ya está en uso")
        return value
    
    def validate_username(self, value):
        if value is None:
            return value
        v = value.strip()
        #Permitir letras, números, punto, guion, guion bajo; 3-30 chars
        if not re.match(r'^[A-Za-z0-9._-]{3,30}$', v):
            raise serializers.ValidationError(
                 "El nombre de usuario sólo puede contener letras, números, ., _ y -, entre 3 y 30 caracteres."
            )
        return v
    
    def validate_password(self, value):
        regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$'
        if not re.match(regex, value):
            raise serializers.ValidationError(
                "La contraseña debe tener mínimo 8 caracteres, una mayúscula, una minúscula, un número y un carácter especial."
            )
        return value
    
    def validate_new_password(self, value):
        regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$'
        if not re.match(regex, value):
            raise serializers.ValidationError(
                "La nueva contraseña debe tener mínimo 8 caracteres, una mayúscula, una minúscula, un número y un carácter especial."
            )
        return value

    #Obtener roles
    def get_roles(self, obj):
        return [{"id": g.id, "name": g.name} for g in obj.groups.all()] 


    def create(self, validated_data):
        # 🔴 CAMBIO: leer roles desde initial_data
        roles_data = self.initial_data.get("roles", [])
        roles_ids = [
            r.get("id") for r in roles_data
            if isinstance(r, dict) and r.get("id")
        ]

        institucion = validated_data.pop("institucion", None)
        password = validated_data.pop("password", None)

        with transaction.atomic():
            user = CustomUser(**validated_data)

            if password:
                user.set_password(password)

            if institucion:
                user.institucion = institucion

            user.save()
            
        return user


    def update(self, instance, validated_data):
        new_password = validated_data.pop('new_password', None)
        if new_password:
            instance.set_password(new_password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)  
        instance.save()

        # Extraer solo IDs de los roles
        roles_data = self.initial_data.get("roles", [])
        roles_ids = [r["id"] for r in roles_data if "id" in r]

        try:
            if roles_ids:
                groups = Group.objects.filter(id__in=roles_ids)
                if not groups.exists():
                    raise serializers.ValidationError({"roles": "Ningún grupo válido fue encontrado."})

                instance.groups.set(groups)

        except Exception as e:
            raise serializers.ValidationError({"roles": f"Error actualizando roles: {str(e)}"})

        return instance
#--------------------
#LISTAS
#--------------------

class UsuarioListSerializer(serializers.ModelSerializer):
    roles=serializers.SerializerMethodField()
    nombre_departamento = serializers.CharField(source='departamento.nombre', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'first_name',
            'second_name',
            'last_name',
            'second_last_name',
            'roles',
            'nombre_departamento',
            'is_active'
        ]
    
    #Para obtener los roles del usuario
    def get_roles(self, obj):
        # Usamos _prefetched_groups si está cargado, si no, caemos a groups.all()
        groups = getattr(obj, "_prefetched_groups", obj.groups.all())
        return [g.name for g in groups]

class DepartamentoListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = ['id', 'nombre', 'sigla', 'estado']

class RolListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']

class PermisosListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename']

# -------------------------------
# SELECTS
# -------------------------------
class DepartamentoSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = ['id', 'nombre']

class RolSelectDualSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']
