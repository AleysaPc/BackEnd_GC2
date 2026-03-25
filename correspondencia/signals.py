from django.db.models.signals import post_save  #Despuesta de guardar un modelo 
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.conf import settings
from .models import Recibida, CorrespondenciaElaborada
from .models import AccionCorrespondencia
from usuario.models import CustomUser
from .tasks import procesar_notificacion_task
import requests
import json
import os

#Objetivo del archivo Detectar eventos del sistema, no ejecutar logica pesada. 
#Si se creo una correspondencia dispara algo"
#Signal es un evento automatico en Django. 

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
    """Enviar email usando EmailJS REST API a múltiples destinatarios"""
    
    if not destinatarios:
        print("No hay destinatarios")
        return False
    
    try:
        public_key = os.environ.get("EMAILJS_PUBLIC_KEY")
        service_id = os.environ.get("EMAILJS_SERVICE_ID")
        template_id = os.environ.get("EMAILJS_TEMPLATE_ID")
        
        print(f"🔧 Enviando emails con EmailJS:")
        print(f"   Service ID: {service_id}")
        print(f"   Template ID: {template_id}")
        print(f"   Destinatarios: {len(destinatarios)}")
        
        # Enviar a cada destinatario
        for destinatario in destinatarios:
            data = {
                'service_id': service_id,
                'template_id': template_id,
                'user_id': public_key,
                'template_params': {
                    'subject': asunto,
                    'message': mensaje,
                    'to_email': destinatario,
                }
            }
            
            response = requests.post(
                'https://api.emailjs.com/api/v1.0/email/send',
                data=json.dumps(data),
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print(f"✅ Email enviado a {destinatario}")
            else:
                print(f"❌ Error enviando a {destinatario}: {response.text}")
                return False
        
        print("📧 Correos enviados correctamente con EmailJS.")
        return True
        
    except Exception as e:
        print(f"❌ Error al enviar correo con EmailJS: {str(e)}")
        return False

#Para el envío de correo en documentos entrantes
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files import File
import os

@receiver(post_save, sender=Recibida)
def enviar_notificacion_recibida(sender, instance, created, **kwargs):
    if not created: #Solo cuando se crea, no cuando se edita
        return

    # Usar transaction.on_commit para asegurar que la transacción se haya completado
    transaction.on_commit(
        lambda: procesar_notificacion_task.delay("recibida", instance.id_correspondencia) #borrando delay
    )                                     #delay envia la tarea a Redis Celery lo ejecuta en segundo plano

# Para el envío de correo en documentos salientes
@receiver(post_save, sender=CorrespondenciaElaborada)
def enviar_notificacion_elaborada(sender,instance, created, **kwargs):
    if not created:
        return
     # Usar transaction.on_commit para asegurar que la transacción se haya completado
    transaction.on_commit(
        lambda: procesar_notificacion_task.delay("elaborada", instance.id_correspondencia) #borrando delay
    )                                     #delay envia la tarea a Redis Celery lo ejecuta en segundo plano

#Para envio de notificación
@receiver(post_save, sender=AccionCorrespondencia)
def crear_notificacion_al_accion(sender, instance, created, **kwargs):
    if created and instance.usuario_destino:
        print(f"Signal: Acción creada para usuario_destino={instance.usuario_destino} con visto={instance.visto}")
        if instance.visto:
            instance.visto = False
            instance.save(update_fields=['visto'])
            print(f"Signal: Modificado visto a False para id={instance.id}")
