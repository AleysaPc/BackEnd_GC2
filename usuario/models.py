from django.db import models
from django.contrib.auth.models import AbstractUser, Permission, Group
from django.contrib.auth.base_user import BaseUserManager

from django_rest_passwordreset.signals import reset_password_token_created
from django.dispatch import receiver 
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings

class CustomUserManager(BaseUserManager): 
    def create_user(self, email, password=None, **extra_fields ): 
        if not email: 
            raise ValueError('Email is a required field')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self,email, password=None, **extra_fields): 
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
    
class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Nombre del rol
    description = models.TextField(blank=True, null=True)  # Descripción opcional

    def __str__(self):
        return self.name

class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    sigla = models.CharField(max_length=10, unique=True)
    estado = models.BooleanField(default=True)  # True = Activo, False = Inactivo
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='departamentos_responsables')

    def __str__(self):
        return f"{self.sigla} - {self.nombre}"


class CustomUser(AbstractUser):
    email = models.EmailField(max_length=200, unique=True)
    birthday = models.DateField(null=True, blank=True)
    username = models.CharField(max_length=200, null=True, blank=True)
    institucion = models.ForeignKey('contacto.Institucion', on_delete=models.SET_NULL, null=True, blank=True)
    secund_name = models.CharField(max_length=100, null=True, blank=True)
    secund_last_name = models.CharField(max_length=100, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True)
 
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email}"
    
