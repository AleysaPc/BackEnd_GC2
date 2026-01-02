#Modelo que representa derivaciones, acciones y usuarios destino
from .models import AccionCorrespondencia
from  usuario.models import CustomUser
#Para acceder a los emails
#Lo usamos para los archivos
import os
from .signals import construir_mensaje, enviar_correo


#Archivo cerebro porque decide a quien enviar, que adjuntar y cuando enviar con que contenido

#Función reutilizable desde signal y celery
def procesar_notificacion(instance): #Celery no tiene request
    print("\n=== Inicio de notificación de correo (Celery) ===")
    print(f"Documento creado - ID: {instance.id_correspondencia}")
    print(f"Número de registro: {instance.nro_registro}")
    print(f"Referencia: {instance.referencia}")

    #Busca destinatarios reales.
    usuarios_ids = AccionCorrespondencia.objects.filter(
        correspondencia=instance                    #Evita duplicados
    ).values_list('usuario_destino__id', flat=True).distinct()
    
    #Si no hay usuario envia al creador?
    if not usuarios_ids:
        usuarios_ids = [instance.usuario.id] if instance.usuario else []

    #Devuelve los emails, filtrando nulos y vacios. 
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

    instance.refresh_from_db() #Importante codigo de Celery que corre en segundo plano
    documentos = instance.documentos.all()

    archivos_para_adjuntar = []

    for doc in documentos: #Verifica si existe archivo
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

    print("=== Fin de notificación ===")
