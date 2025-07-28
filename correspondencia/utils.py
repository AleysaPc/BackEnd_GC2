from io import BytesIO
from django.http import HttpResponse
from docx import Document
from docx.shared import Pt
from django.utils.timezone import now
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import pdfkit
from usuario.models import CustomUser
from .models import AccionCorrespondencia
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


def generar_documento_word(docSaliente):
    """Genera un documento Word a partir de un objeto DocSaliente."""

    doc = Document()

    # Fecha de envío
    if docSaliente.fecha_envio:
        fecha_envio_str = docSaliente.fecha_envio.strftime('%d-%m-%Y')
    else:
        fecha_envio_str = now().strftime('%d-%m-%Y')

    doc.add_paragraph(f"La Paz, {fecha_envio_str}")

    # CITE
    parrafo_cite = doc.add_paragraph()  
    run_cite = parrafo_cite.add_run(f"{docSaliente.cite}")
    run_cite.bold = True

    # Señor:
    doc.add_paragraph("Señor:")

    contacto = docSaliente.contacto  # Acceso seguro al contacto

    if contacto:
        # Obtener título abreviado
        titulo_prof = contacto.titulo_profesional
        titulo_dict = {
            "Ingeniero": "Ing.",
            "Licenciado": "Lic.",
            "Doctor": "Dr.",
            "Abogado": "Abog.",
            "Profesor": "Prof.",
            "Magister": "Mgs.",
        }
        titulo = titulo_dict.get(titulo_prof, "")

        # Agregar datos del contacto
        nombre_completo = f"{titulo} {contacto.nombre_contacto or ''}".strip()
        doc.add_paragraph(nombre_completo)
        doc.add_paragraph(f"{contacto.apellido_pat_contacto or ''} {contacto.apellido_mat_contacto or ''}".strip())
        doc.add_paragraph(contacto.cargo.upper() if contacto.cargo else "")
        doc.add_paragraph(str(contacto.institucion).upper() if contacto.institucion else "")
    else:
        # Contacto no disponible
        doc.add_paragraph("Nombre no disponible")
        doc.add_paragraph("Apellidos no disponibles")
        doc.add_paragraph("Cargo no disponible")
        doc.add_paragraph("Institución no disponible")

    # Presente
    doc.add_paragraph("Presente.-")

    # Referencia alineada a la derecha, subrayada y en negrita
    parrafo_ref = doc.add_paragraph()
    parrafo_ref.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
    run_ref = parrafo_ref.add_run(f"Ref.: {docSaliente.referencia}")
    run_ref.bold = True
    run_ref.underline = True

    # Texto de cortesía
    doc.add_paragraph("De nuestra mayor consideración:")

    # Descripción
    doc.add_paragraph(docSaliente.descripcion)

    # Guardar en buffer
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename=correspondencia_{docSaliente.cite}.docx'

    return response

#DERIVACIÓN
def derivar_correspondencia(correspondencia, usuario_actual, usuarios_destino):
    if not usuarios_destino:
        return

    usuarios_validos = CustomUser.objects.filter(id__in=usuarios_destino)

    for usuario in usuarios_validos:
        # Evitar duplicados
        if not AccionCorrespondencia.objects.filter(
            correspondencia=correspondencia,
            usuario_destino=usuario,
            accion="DERIVAR"
        ).exists():
            AccionCorrespondencia.objects.create(
                correspondencia=correspondencia,
                usuario=usuario_actual,
                usuario_destino=usuario,
                accion="DERIVAR"
            )
