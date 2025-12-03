from jinja2 import Template
from django.utils.timezone import now

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

def renderizar_contenido_html(template_string, context):
    template = Template(template_string)
    return template.render(**context)


def generar_html_desde_objeto(correspondencia_elaborada):
    if not correspondencia_elaborada.plantilla or not correspondencia_elaborada.plantilla.estructura_html:
        return ""
    
    if not correspondencia_elaborada.fecha_elaboracion:
        correspondencia_elaborada.fecha_elaboracion = now()

    fecha = correspondencia_elaborada.fecha_elaboracion
    fecha_formateada = f"{fecha.day} de {MESES_ES[fecha.month]} de {fecha.year}" if fecha else ""

    # Construir datos del contacto incluyendo título profesional
    contacto = correspondencia_elaborada.contacto
    contacto_data = {}
    if contacto:
        # Diccionario de títulos
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

        contacto_data = {
            "nombre_completo": nombre_completo,
            "cargo": contacto.cargo or "",
            "institucion": str(contacto.institucion) if contacto.institucion else "",
            "email": contacto.email or "",
            "telefono": contacto.telefono or "",
        }
    else:
        contacto_data = {
            "nombre_completo": "Nombre no disponible",
            "cargo": "Cargo no disponible",
            "institucion": "Institución no disponible",
        }

    tipo_doc = getattr(correspondencia_elaborada.plantilla, "tipo", "").lower()

    base_context = {
        "fecha_elaboracion": fecha_formateada,
        "cite": correspondencia_elaborada.cite,
        "referencia": correspondencia_elaborada.referencia,
        "elaborado_por": correspondencia_elaborada.usuario.username if correspondencia_elaborada.usuario else "",
        "remitente": correspondencia_elaborada.usuario.username if correspondencia_elaborada.usuario else "",
        "destinatario": contacto_data.get("nombre_completo", ""),
        "contacto": contacto_data,
        "tipo_documento": tipo_doc,
    }

    if tipo_doc == "informe":
        context = {
            **base_context,
            "descripcion_introduccion": correspondencia_elaborada.descripcion_introduccion or "",
            "descripcion_desarrollo": correspondencia_elaborada.descripcion_desarrollo or "",
            "descripcion_conclusion": correspondencia_elaborada.descripcion_conclusion or "",
        }
    else:
        context = {
            **base_context,
            "descripcion": correspondencia_elaborada.descripcion or "",
        }

    return renderizar_contenido_html(correspondencia_elaborada.plantilla.estructura_html, context)
