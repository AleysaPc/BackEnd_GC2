from docx import Document
from django.utils.timezone import now

def crear_documento():
    return Document()

def obtener_fecha(fecha_envio):
    return fecha_envio or now()
