from django.contrib import admin
from .models import Correspondencia, DocEntrante, DocSaliente
# Register your models here.
admin.site.register(Correspondencia)
admin.site.register(DocEntrante)
admin.site.register(DocSaliente)