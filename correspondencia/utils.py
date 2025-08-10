from io import BytesIO
from django.http import HttpResponse
from docx import Document
from docx.shared import Pt
from django.utils.timezone import now
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import pdfkit
from usuario.models import CustomUser

from jinja2 import Template

def renderizar_contenido_html(template_string, context):
    template = Template(template_string)
    return template.render(context)

import pdfkit

# Ruta absoluta al ejecutable 
RUTA_WKHTMLTOPDF = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"

config = pdfkit.configuration(wkhtmltopdf=RUTA_WKHTMLTOPDF)

def generar_pdf_desde_html(html_content):
    options = {
        'enable-local-file-access': None
    }
    pdf = pdfkit.from_string(html_content, False, options=options, configuration=config)
    return pdf

#GENERAR DOCUMENTO WORD

def generar_documento_word(correspondenciaElaborada):
    doc = Document()

    fecha_envio_str = correspondenciaElaborada.fecha_envio.strftime('%d-%m-%Y') if correspondenciaElaborada.fecha_envio else now().strftime('%d-%m-%Y')
    doc.add_paragraph(f"La Paz, {fecha_envio_str}")

    parrafo_cite = doc.add_paragraph()
    run_cite = parrafo_cite.add_run(f"{correspondenciaElaborada.cite}")
    run_cite.bold = True

    doc.add_paragraph("Señor:")

    contacto = correspondenciaElaborada.contacto
    if contacto:
        titulo_dict = {
            "Ingeniero": "Ing.",
            "Licenciado": "Lic.",
            "Doctor": "Dr.",
            "Abogado": "Abog.",
            "Profesor": "Prof.",
            "Magister": "Mgs.",
        }
        titulo = titulo_dict.get(contacto.titulo_profesional, "")
        nombre_completo = f"{titulo} {contacto.nombre_contacto or ''} {contacto.apellido_pat_contacto or ''} {contacto.apellido_mat_contacto or ''}".strip()
        doc.add_paragraph(nombre_completo)
        doc.add_paragraph(contacto.cargo.upper() if contacto.cargo else "")
        doc.add_paragraph(str(contacto.institucion).upper() if contacto.institucion else "")
    else:
        doc.add_paragraph("Nombre no disponible")
        doc.add_paragraph("Apellidos no disponibles")
        doc.add_paragraph("Cargo no disponible")
        doc.add_paragraph("Institución no disponible")

    doc.add_paragraph("Presente.-")

    parrafo_ref = doc.add_paragraph()
    parrafo_ref.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
    run_ref = parrafo_ref.add_run(f"Ref.: {correspondenciaElaborada.referencia}")
    run_ref.bold = True
    run_ref.underline = True

    doc.add_paragraph("De nuestra mayor consideración:")
    doc.add_paragraph(correspondenciaElaborada.descripcion)
    doc.add_paragraph("Sin otro particular, nos despedimos con las consideraciones más distinguidas.")
    doc.add_paragraph("Atentamente,")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    filename = f"correspondencia_{correspondenciaElaborada.cite}.docx"

    return buffer, filename

#DERIVACIÓN
def derivar_correspondencia(correspondencia, usuario_actual, usuarios_destino, comentario_derivacion):
    from .models import AccionCorrespondencia
    if not usuarios_destino:
        return

    # Proporcionar una cadena vacía si comentario_derivacion es None
    comentario_derivacion = comentario_derivacion or ""

    usuarios_validos = CustomUser.objects.filter(id__in=usuarios_destino)

    for usuario in usuarios_validos:
        # Evitar duplicados
        if not AccionCorrespondencia.objects.filter(
            correspondencia=correspondencia,
            usuario_destino=usuario,
            accion="DERIVADO",
            comentario=comentario_derivacion
        ).exists():
            AccionCorrespondencia.objects.create(
                correspondencia=correspondencia,
                usuario=usuario_actual,
                usuario_destino=usuario,
                accion="DERIVADO",
                comentario=comentario_derivacion
            )