from django.contrib import admin
from .models import CustomUser,Departamento,Role

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Departamento)
admin.site.register(Role)
