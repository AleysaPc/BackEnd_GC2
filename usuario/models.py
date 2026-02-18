from django.db import models
from django.contrib.auth.models import AbstractUser, Permission, Group
from django.contrib.auth.base_user import BaseUserManager

from django_rest_passwordreset.signals import reset_password_token_created
from django.dispatch import receiver 
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist
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

class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    sigla = models.CharField(max_length=10, unique=True)
    estado = models.BooleanField(default=True)  # True = Activo, False = Inactivo

    def __str__(self):
        return f"{self.sigla} - {self.nombre}"


class CustomUser(AbstractUser):
    email = models.EmailField(max_length=200, unique=True)
    birthday = models.DateField(null=True, blank=True)
    username = models.CharField(max_length=200, null=True, blank=True)
    institucion = models.ForeignKey('contacto.Institucion', on_delete=models.SET_NULL, null=True, blank=True)
    second_name = models.CharField(max_length=100, null=True, blank=True)
    second_last_name = models.CharField(max_length=100, null=True, blank=True)
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True)
    lugar_nacimiento = models.CharField(max_length=100, null=True, blank=True)
    documento_identidad = models.CharField(max_length=100, null=True, blank=True)
    direccion = models.CharField(max_length=100, null=True, blank=True)
    telefono = models.CharField(max_length=100, null=True, blank=True)
    celular = models.CharField(max_length=100, null=True, blank=True)
    cargo = models.CharField(max_length=100, null=True, blank=True)
    imagen = models.ImageField(upload_to='usuarios/', null=True, blank=True)
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email}"
    
@receiver(reset_password_token_created)
def password_reset_token_created(reset_password_token, *args, **kwargs):
    sitelink = "http://localhost:5173/"
    token = "{}".format(reset_password_token.key)
    full_link = sitelink + "password-reset/" + token

    context = {
        'full_link': full_link,
        'email_adress': reset_password_token.user.email
    }

    try:
        html_message = render_to_string("email.html", context=context)
    except TemplateDoesNotExist:
        # Fallback para evitar error 500 si la plantilla no se carga en runtime.
        html_message = (
            "<p>Hola,</p>"
            "<p>Recibimos una solicitud para restablecer tu contraseña.</p>"
            f"<p><a href='{full_link}'>{full_link}</a></p>"
            "<p>Si no solicitaste este cambio, puedes ignorar este correo.</p>"
            f"<p>Correo asociado: {reset_password_token.user.email}</p>"
        )
    plain_message = strip_tags(html_message)

    msg = EmailMultiAlternatives(
        subject=f"Request for resetting password for {reset_password_token.user.email}", 
        body=plain_message,
        from_email="sender@example.com", 
        to=[reset_password_token.user.email]
    )

    msg.attach_alternative(html_message, "text/html")
    msg.send()
