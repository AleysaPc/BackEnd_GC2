from django.utils import timezone
from rest_framework.exceptions import ValidationError


# =========================
# FECHA NO FUTURA
# =========================
def validar_fecha_no_futura(fecha, campo):
    if fecha and fecha > timezone.now():
        raise ValidationError({
            campo: "La fecha no puede ser futura."
        })


# =========================
# RANGO DE FECHAS
# =========================
def validar_rango_fechas(fecha_inicio, fecha_fin, campo_inicio, campo_fin):
    if fecha_inicio and fecha_fin:
        if fecha_fin < fecha_inicio:
            raise ValidationError({
                campo_fin: f"{campo_fin} no puede ser menor que {campo_inicio}"
            })


# =========================
# ORDEN LÓGICO (FLUJO)
# =========================
def validar_orden_logico_fechas(*fechas):
    """
    Ejemplo:
    validar_orden_logico_fechas(
        (fecha_recepcion, "recepción"),
        (fecha_respuesta, "respuesta"),
        (fecha_envio, "envío")
    )
    """

    prev_fecha = None
    prev_nombre = None

    for fecha, nombre in fechas:
        if fecha:
            if prev_fecha and fecha < prev_fecha:
                raise ValidationError({
                    nombre: f"{nombre} no puede ser anterior a {prev_nombre}"
                })
            prev_fecha = fecha
            prev_nombre = nombre