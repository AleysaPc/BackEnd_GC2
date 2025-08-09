from jinja2 import Template

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
    return template.render(context)

def generar_html_desde_objeto(correspondencia_elaborada):
    if not correspondencia_elaborada.plantilla or not correspondencia_elaborada.plantilla.estructura_html:
        return ""

    fecha = correspondencia_elaborada.fecha_elaboracion
    fecha_formateada = f"{fecha.day} de {MESES_ES[fecha.month]} de {fecha.year}" if fecha else ""

    contacto = correspondencia_elaborada.contacto
    contacto_data = {}
    if contacto:
        contacto_data = {
            "nombre_contacto": contacto.nombre_contacto or "",
            "apellido_pat_contacto": contacto.apellido_pat_contacto or "",
            "apellido_mat_contacto": contacto.apellido_mat_contacto or "",
            "titulo_profesional": contacto.titulo_profesional or "",
            "cargo": contacto.cargo or "",
            "email": contacto.email or "",
            "telefono": contacto.telefono or "",
            "institucion": str(contacto.institucion) if contacto.institucion else "",
        }

    context = {
        "fecha_elaboracion": fecha_formateada,
        "cite": correspondencia_elaborada.cite,
        "referencia": correspondencia_elaborada.referencia,
        "descripcion": correspondencia_elaborada.descripcion,
        "gestion": correspondencia_elaborada.gestion,
        "elaborado_por": correspondencia_elaborada.usuario.username if correspondencia_elaborada.usuario else "",
        "contacto": contacto_data,
    }

    return renderizar_contenido_html(correspondencia_elaborada.plantilla.estructura_html, context)
