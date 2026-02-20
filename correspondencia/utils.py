#Para la elaboraciónd e documentos word y pdf
from io import BytesIO
from django.http import HttpResponse
from docx import Document
from docx.shared import Pt
from django.utils.timezone import now
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import pdfkit
from usuario.models import CustomUser
from jinja2 import Template
import os
import shutil

def renderizar_contenido_html(template_string, context):
    template = Template(template_string)
    return template.render(context)

def get_pdfkit_config():
    #1) Permite fijar ruta por variable de entorno (Railway/local)
    #2) Si no existe, busca "WKHTMLTOPDF_PATH" en Path del sistema

    wkhtml_path = os.getenv("WKHTMLTOPDF_PATH") or shutil.which("wkhtmltopdf")
    if not wkhtml_path:
        raise RuntimeError(
            "wkhtmltopdf no está instalado o no está en Path"
            "Instalalo o define WKHTMLTOPDF_PATH"
        )
    return pdfkit.configuration(wkhtmltopdf=wkhtml_path)

def generar_pdf_desde_html(html_content):
    # Get the base directory of your Django project
    import os
    from django.conf import settings
    
    # Build absolute paths to your header and footer
    header_path = os.path.join(settings.BASE_DIR, 'documento', 'templates', 'Documento', 'header.html')
    footer_path = os.path.join(settings.BASE_DIR, 'documento', 'templates', 'Documento', 'footer.html')

    options = {
        'page-size': 'Letter',
        'margin-top': '5cm',
        'margin-bottom': '3cm',
        'margin-left': '2.5cm',
        'margin-right': '2.5cm',
        'header-html': header_path,
        'footer-html': footer_path,
        'zoom': '1.0',
        'disable-smart-shrinking': '',
        'enable-local-file-access': '',
        'encoding': 'UTF-8',
    }
    config = get_pdfkit_config()
    return pdfkit.from_string(
        html_content,
        False,
        options=options,
        configuration=config,
    )

#GENERAR DOCUMENTO WORD
from django.utils.html import strip_tags
import html

from .services.word.nota import generar_nota_word
from .services.word.informe import generar_informe_word
from .services.word.convocatoria import generar_convocatoria_word
from .services.word.comunicado import generar_comunicado_word
from .services.word.resolucion import generar_resolucion_word
from .services.word.memorando import generar_memorando_word

# Diccionario de dispatch para cada tipo de documento
GENERADORES_WORD = {
    "nota": generar_nota_word,
    "informe": generar_informe_word,
    "memorando": generar_memorando_word,
    "convocatoria": generar_convocatoria_word,
    "comunicado": generar_comunicado_word,
    "resolucion": generar_resolucion_word
}

def generar_documento_word(correspondenciaElaborada):
    """
    Generador principal de documentos Word.
    Selecciona el generador según el tipo de documento.
    Funciona aunque:
      - No haya documentos asociados.
      - Haya varios documentos asociados.
    """
    # 1️⃣ Tomar el primer documento relacionado (si existe)
    doc_rel = correspondenciaElaborada.documentos.first()

    # 2️⃣ Determinar tipo de documento
    if getattr(correspondenciaElaborada, "plantilla", None):
        tipo = correspondenciaElaborada.plantilla.tipo
    else:
        tipo = getattr(doc_rel, "tipo_documento", "nota")

    tipo = (tipo or "nota").lower()

    # 3️⃣ Seleccionar función generadora según tipo
    generador = GENERADORES_WORD.get(tipo)
    if not generador:
        raise ValueError(f"No se encontró generador Word para tipo: {tipo}")

    # 4️⃣ Llamar al generador correspondiente
    return generador(correspondenciaElaborada)



#DERIVACIÓN
def derivar_correspondencia(correspondencia, usuario_origen, usuario_destino, comentario_derivacion):
    from .models import AccionCorrespondencia
    if not usuario_destino:
        return

    # Proporcionar una cadena vacía si comentario_derivacion es None
    comentario_derivacion = comentario_derivacion or ""

    usuarios_validos = CustomUser.objects.filter(id__in=usuario_destino)

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
                usuario_origen=usuario_origen,
                usuario_destino=usuario,
                accion="DERIVADO",
                comentario=comentario_derivacion
            )