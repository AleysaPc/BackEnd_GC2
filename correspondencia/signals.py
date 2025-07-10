from django.db.models.signals import post_save 
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.conf import settings
from .models import Recibida, Enviada, Interna
import os


# Función para construir el mensaje del correo
def construir_mensaje(nro_registro, referencia, remitente, fecha_respuesta_formateada):
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
    mensaje += f'Fecha límite de respuesta: {fecha_respuesta_formateada or "No requiere respuest"}\n'
    
    return mensaje

# Función para enviar el correo con adjunto
def enviar_correo(asunto, mensaje, archivo=None):
    destinatarios = ['isabella172813@gmail.com']
    email = EmailMessage(
        asunto,
        mensaje,
        'isatest172813@gmail.com',  # Remitente
        destinatarios,  # Lista de destinatarios
    )
    
    if archivo:
        email.attach_file(archivo.path)
    
    try:
        email.send(fail_silently=False)
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

# Para el envío de correo en documentos entrantes
#@receiver(post_save, sender=Recibida)
#def enviar_notificacion_correo(sender, instance, created, **kwargs):
 #   nro_registro = instance.nro_registro
 #   referencia = instance.referencia

 #   if created:  # Solo si se crea un nuevo documento
 #       print("Documento creado")

 #   fecha_respuesta_formateada = instance.fecha_respuesta.strftime('%d/%m/%Y %H:%M') if instance.fecha_respuesta else None
 #   mensaje = construir_mensaje(nro_registro, referencia, instance.contacto, fecha_respuesta_formateada)
    
    # Para adjuntar el documento
 #   documentos = instance.documentos.all()  # Accede a los documentos asociados a esta instancia de DocEntrante (que es una subclase de Correspondencia)

 #   if documentos.exists():
 #       documento = documentos.first()  # Si hay documentos, toma el primero
 #       print(f"Documento adjunto: {documento.archivo.path}")  # Esto es solo para depurar
 #       enviar_correo(f'Nuevo documento registrado: {nro_registro}', mensaje, documento.archivo)
 #   else:
 #       print("No hay documentos asociados a la correspondencia")
 #       enviar_correo(f'Nuevo documento registrado: {nro_registro}', mensaje)
        
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

        archivo = None
        if instance.archivo_word:
            ruta_documento = os.path.join(settings.MEDIA_ROOT, instance.archivo_word.name)
            if os.path.exists(ruta_documento):
                archivo = instance.archivo_word

        enviar_correo(f'Nuevo documento elaborado: {cite}', mensaje, archivo)
