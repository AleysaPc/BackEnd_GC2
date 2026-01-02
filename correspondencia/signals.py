from django.db.models.signals import post_save 
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.conf import settings
from .models import Recibida, Enviada
from .models import AccionCorrespondencia
from usuario.models import CustomUser
from .tasks import procesar_notificacion_task



# Función para construir el mensaje del correo
def construir_mensaje(nro_registro, referencia, remitente, fecha_respuesta):
    if remitente:
        nombre_remitente = f"{remitente.nombre_contacto} {remitente.apellido_pat_contacto} {remitente.apellido_mat_contacto}"
        cargo_remitente = remitente.cargo
        empresa_remitente = remitente.institucion.razon_social if remitente.institucion else 'No especificado'
    else:
        nombre_remitente = 'No especificado'
        cargo_remitente = 'No especificado'
        empresa_remitente = 'No especificado'

    mensaje = f'Se ha registrado un nuevo documento con los siguientes detalles:\n\n'
    mensaje += f'Número de registro: {nro_registro}\n'
    mensaje += f'Referencia: {referencia}\n'
    mensaje += f'Remitente: {nombre_remitente}\n'
    mensaje += f'Cargo: {cargo_remitente}\n'
    mensaje += f'Empresa: {empresa_remitente}\n'
    if fecha_respuesta:
        mensaje += f'Fecha límite de respuesta: {fecha_respuesta}\n'
    else:
        mensaje += 'Fecha límite de respuesta: No requiere respuesta\n'

    
    return mensaje

def enviar_correo(asunto, mensaje, destinatarios, archivos=None):

    #destinatarios = ['isabella172813@gmail.com']
    #email = EmailMessage(
        #mensaje,
        #asunto,
        #'isatest172813@gmail.com',  # remitente
        #destinatarios,
    #)

    if not destinatarios:
        print("No hay destinatarios")
        return False
    
    email = EmailMessage(
        subject=asunto,
        body=mensaje,
        from_email='isatest172813@gmail.com',
        to=destinatarios,
    )

    if archivos:
        for archivo in archivos:
            try:
                print(f"Adjuntando archivo: {archivo.name}")
                # Si es un objeto File de Django, ya está listo para adjuntar
                email.attach(archivo.name, archivo.read(), 'application/octet-stream')
            except Exception as e:
                print(f"Error al adjuntar archivo: {str(e)}")

    try:
        email.send(fail_silently=False)
        print("Correo enviado correctamente.")
    except Exception as e:
        print("Error al enviar correo:", str(e))

#Para el envío de correo en documentos entrantes
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files import File
import os

@receiver(post_save, sender=Recibida)
def enviar_notificacion_correo(sender, instance, created, **kwargs):
    if not created:
        return

    # Usar transaction.on_commit para asegurar que la transacción se haya completado
    transaction.on_commit(
        lambda: procesar_notificacion_task.delay(instance.id_correspondencia)
    )

# Para el envío de correo en documentos salientes
@receiver(post_save, sender=Enviada)
def enviar_notificacion_correo(sender, instance, created, **kwargs):
    if instance.estado == "en_revision":  # Solo enviar si el estado es "en_revision"
        cite = instance.cite
        referencia = instance.referencia
        destinatario = instance.contacto
        estado = instance.estado

        mensaje = f'Se ha elaborado un nuevo documento con los siguientes detalles:\n\n'
        mensaje += f'Nro. CITE: {cite}\n'
        mensaje += f'Referencia: {referencia}\n'

        if destinatario:
            mensaje += f'Destinatario: {destinatario.nombre_contacto} {destinatario.apellido_pat_contacto} {destinatario.apellido_mat_contacto}\n'
            mensaje += f'Cargo: {destinatario.cargo}\n'
            mensaje += f'Empresa: {destinatario.institucion.razon_social if destinatario.institucion else "No especificado"}\n'
        else:
            mensaje += 'Destinatario: No especificado\nCargo: No especificado\nEmpresa: No especificado\n'

        mensaje += f'Estado: {estado}\n'

        archivos_para_adjuntar = []

        if instance.archivo_word:
            archivos_para_adjuntar.append(instance.archivo_word)

        enviar_correo(f'Nuevo documento elaborado: {cite}', mensaje, archivos_para_adjuntar if archivos_para_adjuntar else None)


#Para envio de notificación
@receiver(post_save, sender=AccionCorrespondencia)
def crear_notificacion_al_accion(sender, instance, created, **kwargs):
    if created and instance.usuario_destino:
        print(f"Signal: Acción creada para usuario_destino={instance.usuario_destino} con visto={instance.visto}")
        if instance.visto:
            instance.visto = False
            instance.save(update_fields=['visto'])
            print(f"Signal: Modificado visto a False para id={instance.id}")
