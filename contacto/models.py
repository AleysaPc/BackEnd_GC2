from django.db import models

# Create your models here.
class Institucion (models.Model):
    id_institucion = models.AutoField(primary_key=True)
    razon_social = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    fecha_fundacion = models.DateField()

    def __str__(self):
        return self.razon_social
    
class Contacto(models.Model):
    TIPO_CONTACTO_CHOICES = [
        ('afiliado', 'Afiliado'),
        ('externo', 'Externo'),
    ]

    tipo_contacto = models.CharField(
        max_length=20,
        choices=TIPO_CONTACTO_CHOICES, null=True, blank=True,
    )
    id_contacto = models.AutoField(primary_key=True)
    nombre_contacto = models.CharField(max_length=100)
    apellido_pat_contacto = models.CharField(max_length=100)
    apellido_mat_contacto = models.CharField(max_length=100)
    titulo_profesional = models.CharField(max_length=100, null=True, blank=True)
    cargo = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    institucion = models.ForeignKey(Institucion, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.nombre_contacto} {self.apellido_pat_contacto} - {self.cargo} - {self.institucion}"