from .models import AccionCorrespondencia
from usuario.models import CustomUser
import os

from .signals import construir_mensaje, enviar_correo


# ==============================
# 📥 NOTIFICACIÓN RECIBIDA
# ==============================
def procesar_notificacion(instance):
    print("\n=== Inicio de notificación (Recibida) ===")

    usuarios_ids = AccionCorrespondencia.objects.filter(
        correspondencia=instance
    ).values_list('usuario_destino__id', flat=True).distinct()

    if not usuarios_ids:
        usuarios_ids = [instance.usuario.id] if instance.usuario else []

    emails = list(
        CustomUser.objects
        .filter(id__in=usuarios_ids)
        .exclude(email__isnull=True)
        .exclude(email__exact="")
        .values_list("email", flat=True)
    )

    if not emails:
        print("No hay destinatarios")
        return

    instance.refresh_from_db()

    documentos = instance.documentos.all()
    archivos_para_adjuntar = []

    for doc in documentos:
        if doc.archivo and os.path.exists(doc.archivo.path):
            archivos_para_adjuntar.append(doc.archivo)

    mensaje = construir_mensaje(
        instance.nro_registro,
        instance.referencia,
        instance.contacto,
        instance.fecha_respuesta,
    )

    enviar_correo(
        asunto=f'Nuevo documento registrado: {instance.nro_registro}',
        mensaje=mensaje,
        destinatarios=emails,
        archivos=archivos_para_adjuntar if archivos_para_adjuntar else None
    )

    print("=== Fin de notificación (Recibida) ===")


# ==============================
# 📤 NOTIFICACIÓN ELABORADA
# ==============================
def procesar_notificacion_elaborada(instance):
    print("\n=== Inicio de notificación (Elaborada) ===")

    # Puedes usar la misma lógica de destinatarios
    usuarios_ids = AccionCorrespondencia.objects.filter(
        correspondencia=instance
    ).values_list('usuario_destino__id', flat=True).distinct()

    if not usuarios_ids:
        usuarios_ids = [instance.usuario.id] if instance.usuario else []

    emails = list(
        CustomUser.objects
        .filter(id__in=usuarios_ids)
        .exclude(email__isnull=True)
        .exclude(email__exact="")
        .values_list("email", flat=True)
    )

    if not emails:
        print("No hay destinatarios")
        return

    instance.refresh_from_db()

    archivos_para_adjuntar = []

    documentos = instance.documentos.all()
    for doc in documentos:
        if doc.archivo and os.path.exists(doc.archivo.path):
            archivos_para_adjuntar.append(doc.archivo)

   # Mensaje propio para elaboradas
    mensaje = f"""
    Se ha elaborado un nuevo documento:

    CITE: {instance.cite}
    Referencia: {instance.referencia}
    Estado: {instance.estado}

    Puedes ver el documento en el siguiente enlace:
    https://backendgc2-production.up.railway.app/api/v1/correspondencia/elaborada/{instance.id_correspondencia}/pdf/
    """
    #http://localhost:8000/api/v1/correspondencia/elaborada/{instance.id_correspondencia}/pdf/

    enviar_correo(
        asunto=f'Nuevo documento elaborado: {instance.cite}',
        mensaje=mensaje,
        destinatarios=emails,
        archivos=archivos_para_adjuntar if archivos_para_adjuntar else None
    )

    print("=== Fin de notificación (Elaborada) ===")