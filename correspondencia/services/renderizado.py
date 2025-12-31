#Renderizado.py se encarga de armar todo el HTML a partir del objeto de correspondencia.

from jinja2 import Template #Se usa para renderizar plantillas HTML dinámicamente
from django.utils.timezone import now #Obtiene la fecha y hora actual considerando la zona horaria de Django.
from pathlib import Path #Para construir rutas absolutas a archivos del proyecto (ej. templates base).
from django.conf import settings

#Para construir rutas absolutas a archivos del proyecto (ej. templates base).
MESES_ES = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}
#Recibe un string de plantilla HTML y un diccionario de contexto.
                              #Lo convierte en un objeto Jinja2 para procesar las variables y sustituir los placeholders.
def renderizar_contenido_html(template_string, context):
    template = Template(template_string)
    return template.render(**context)
                    #Reemplaza las variables de la plantilla con los valores del contexto.

#Función Principal: Genera HTML a partir de un objeto de correspondencia elaborada
#Recibe un objeto CorrespondenciaElaborada y devuelve un string HTML renderizado
def generar_html_desde_objeto(correspondencia_elaborada):
    if not correspondencia_elaborada.plantilla or not correspondencia_elaborada.plantilla.estructura_html:
        return ""
    
    if not correspondencia_elaborada.fecha_elaboracion:
        correspondencia_elaborada.fecha_elaboracion = now()

    #Si el documento no tiene fecha de elaboración, se asigna la fecha actual.
    fecha = correspondencia_elaborada.fecha_elaboracion
    fecha_formateada = f"{fecha.day} de {MESES_ES[fecha.month]} de {fecha.year}" if fecha else ""

    # Construir nombre completo del usuario que elabora
    usuario_obj = correspondencia_elaborada.usuario
    if usuario_obj:
        nombre_completo_usuario = " ".join(
            filter(None, [ #elimina valores vacíos
                getattr(usuario_obj, "first_name", ""),
                getattr(usuario_obj, "secund_name", ""),
                getattr(usuario_obj, "last_name", ""),
                getattr(usuario_obj, "secund_last_name", ""),
            ])
        )
    else:
        nombre_completo_usuario = "Usuario no disponible"

    tipo_doc = getattr(correspondencia_elaborada.plantilla, "tipo", "").lower() #Obtiene el tipo de plantilla

    # Construir datos del destinatario (externo o interno)
    destinatario_data = {}

    # Caso 1: Contacto externo
    if correspondencia_elaborada.contacto:
        contacto = correspondencia_elaborada.contacto
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
        
        destinatario_data = {
            "nombre_completo": nombre_completo,
            "cargo": contacto.cargo or "",
            "institucion": str(contacto.institucion) if contacto.institucion else "",
            "email": contacto.email or "",
            "telefono": contacto.telefono or "",
        }

    # Caso 2: Destino interno
    elif hasattr(correspondencia_elaborada, "destino_interno") and correspondencia_elaborada.destino_interno:
        usuario_destino = correspondencia_elaborada.destino_interno
        nombre_completo = " ".join(
            filter(None, [
                getattr(usuario_destino, "first_name", ""),
                getattr(usuario_destino, "secund_name", ""),
                getattr(usuario_destino, "last_name", ""),
                getattr(usuario_destino, "secund_last_name", ""),
            ])
        )
        destinatario_data = {
            "nombre_completo": nombre_completo,
            "cargo": getattr(usuario_destino, "cargo", ""),
            "institucion": getattr(usuario_destino, "institucion", ""),
            "email": getattr(usuario_destino, "email", ""),
            "telefono": getattr(usuario_destino, "telefono", ""),
        }

    # Caso 3: Ninguno definido
    else:
        destinatario_data = {
            "nombre_completo": "Nombre no disponible",
            "cargo": "Cargo no disponible",
            "institucion": "Institución no disponible",
        }

    # Construcción del contexto base
    #Este diccionario se pasa al HTML para reemplazar todas las variables.
    base_context = {
        "fecha_elaboracion": fecha_formateada,
        "cite": correspondencia_elaborada.cite,
        "referencia": correspondencia_elaborada.referencia,
        "usuario": nombre_completo_usuario,
        "elaborado_por": nombre_completo_usuario,
        "remitente": nombre_completo_usuario,
        "destinatario": destinatario_data.get("nombre_completo", ""),
        "contacto": destinatario_data,
        "tipo_documento": tipo_doc,
    }

    # Agregar campos específicos según tipo de documento
    if tipo_doc in ["informe", "convocatoria"]:
        context = {
            **base_context,
            "descripcion_introduccion": correspondencia_elaborada.descripcion_introduccion or "",
            "descripcion_desarrollo": correspondencia_elaborada.descripcion_desarrollo or "",
            "descripcion_conclusion": correspondencia_elaborada.descripcion_conclusion or "",
        }
    else:  # memorando u otros
        context = {
            **base_context,
            "descripcion_desarrollo": correspondencia_elaborada.descripcion_desarrollo or "",
            "descripcion": correspondencia_elaborada.descripcion or "",
        }

    # Renderizar el contenido HTML
    #Llama a la función de Jinja2 para reemplazar todas las variables de la plantilla con los datos del contexto.
    contenido = renderizar_contenido_html(correspondencia_elaborada.plantilla.estructura_html, context)

    # Ruta del template base
    base_template_path = Path(settings.BASE_DIR) / "documento" / "templates" / "Documento" / "base_documento.html"
    base_template_string = base_template_path.read_text(encoding="utf-8")
    base_template = Template(base_template_string)

    # Renderizar HTML final
    # Combina el contenido renderizado con el template base para crear el documento final
    html_final = base_template.render(
        contenido=contenido,
        membrete_superior='http://localhost:8000/media/Membrete.PNG',
        membrete_inferior='http://localhost:8000/media/MembreteInferior.PNG',
    )

    # Devolver el HTML final listo para generar el PDF
    # Este HTML contiene todo el contenido renderizado y el diseño base
    # Puede ser usado directamente por la función de generación de PDF
    # El HTML incluye las imágenes de membrete y el contenido renderizado
    # Las rutas de las imágenes son relativas al servidor Django y deben estar disponibles en producción
    return html_final
