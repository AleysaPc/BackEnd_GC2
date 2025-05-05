from django.db import models

# Create your models here.
class Institucion (models.Model):
    id_institucion = models.AutoField(primary_key=True)
    razon_social = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    fecha_fundación = models.DateField()

    def __str__(self):
        return self.razon_social
    
class Contacto(models.Model):
    id_contacto = models.AutoField(primary_key=True)
    nombre_contacto = models.CharField(max_length=100)
    apellido_pat_contacto = models.CharField(max_length=100)
    apellido_mat_contacto = models.CharField(max_length=100)
    titulo_profesional = models.CharField(max_length=100, null=True, blank=True)
    cargo = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    institucion = models.ForeignKey(Institucion, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.nombre_contacto} {self.apellido_pat_contacto} - {self.cargo} - {self.institucion}"