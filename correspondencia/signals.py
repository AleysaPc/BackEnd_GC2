from django.db.models.signals import post_save 
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.conf import settings
from .models import Recibida, Enviada
import os
from .models import AccionCorrespondencia
from usuario.models import CustomUser



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

def enviar_correo(asunto, mensaje, archivos=None):
    destinatarios = ['isabella172813@gmail.com']
    email = EmailMessage(
        asunto,
        mensaje,
        'isatest172813@gmail.com',  # remitente
        destinatarios,
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
    transaction.on_commit(lambda: _procesar_notificacion(instance))

def _procesar_notificacion(instance):
    print("\n=== Inicio de notificación de correo (después de commit) ===")
    print(f"Documento creado - ID: {instance.id_correspondencia}")
    print(f"Número de registro: {instance.nro_registro}")
    print(f"Referencia: {instance.referencia}")
    
    # Forzar la recarga de la instancia para asegurar que tenemos los datos más recientes
    from django.db import connection
    connection.close()  # Cerrar la conexión para forzar una nueva
    instance.refresh_from_db()
    
    # Obtener todos los documentos asociados
    documentos = instance.documentos.all()
    print(f"\nDocumentos asociados encontrados: {documentos.count()}")
    
    archivos_para_adjuntar = []

    for i, doc in enumerate(documentos, 1):
        print(f"\nProcesando documento {i}:")
        print(f"  - ID del documento: {doc.id_documento}")
        print(f"  - Nombre del documento: {doc.nombre_documento}")
        print(f"  - Ruta del archivo: {doc.archivo.path if doc.archivo else 'Ninguna'}")
        
        if doc.archivo:
            try:
                # Verificar que el archivo existe
                if not os.path.exists(doc.archivo.path):
                    print(f"  ✗ El archivo no existe en: {doc.archivo.path}")
                    continue
                    
                # Verificar que el archivo no esté vacío
                if doc.archivo.size == 0:
                    print("  ✗ El archivo está vacío")
                    continue
                    
                # Intentar leer el archivo
                with open(doc.archivo.path, 'rb') as f:
                    file_content = f.read()
                    print(f"  - Tamaño leído: {len(file_content)} bytes")
                    # Usar File para crear un nuevo objeto de archivo
                    from django.core.files import File
                    archivos_para_adjuntar.append(File(open(doc.archivo.path, 'rb'), name=os.path.basename(doc.archivo.name)))
                    print("  ✓ Documento listo para adjuntar")
            except Exception as e:
                print(f"  ✗ Error al procesar el archivo: {str(e)}")
        else:
            print("  ✗ No hay archivo asociado a este documento")

    if archivos_para_adjuntar:
        print(f"\nEnviando correo con {len(archivos_para_adjuntar)} archivos adjuntos")
        mensaje = construir_mensaje(
            instance.nro_registro, 
            instance.referencia, 
            instance.contacto, 
            instance.fecha_respuesta,
        )
        enviar_correo(f'Nuevo documento registrado: {instance.nro_registro}', mensaje, archivos_para_adjuntar)
        
        # Cerrar los archivos después de usarlos
        for archivo in archivos_para_adjuntar:
            try:
                archivo.close()
            except:
                pass
    else:
        print("\nNo hay documentos válidos para adjuntar")
        mensaje = construir_mensaje(
            instance.nro_registro, 
            instance.referencia, 
            instance.contacto, 
            instance.fecha_respuesta,
        )
        enviar_correo(f'Nuevo documento registrado: {instance.nro_registro}', mensaje)
    
    print("=== Fin de notificación de correo ===\n")

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
