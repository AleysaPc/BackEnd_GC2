# alertas/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from correspondencia.models import Recibida, Enviada, CorrespondenciaElaborada, AccionCorrespondencia
from .services import crear_alerta_segura

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Recibida)
def crear_alerta_inmediata_recibida(sender, instance, created, **kwargs):
    """Crea alerta automática inmediata al crear o actualizar documento recibido"""
    logger.info(f"Signal Recibida ejecutado - created: {created}")
    logger.info(f"Documento ID: {instance.id_correspondencia}")
    logger.info(f"Fecha respuesta: {instance.fecha_respuesta}")
    logger.info(f"Usuario: {instance.usuario}")
    
    # Si es actualización y ahora tiene usuario y fecha_respuesta
    if not created and instance.usuario and instance.fecha_respuesta:
        logger.info("Actualización con usuario y fecha_respuesta, evaluando...")
    
    # Solo si tiene fecha_respuesta y usuario responsable
    if instance.fecha_respuesta and instance.usuario:
        hoy = timezone.now()
        logger.info(f"Hoy: {hoy}")
        
        # Evaluar fecha inmediatamente
        if instance.fecha_respuesta <= hoy + timezone.timedelta(hours=24):
            if instance.fecha_respuesta <= hoy:
                # Documento vencido
                tipo_alerta = 'vencido'
                nivel_alerta = 'critica'
                logger.info("Creando alerta VENCIDO")
            else:
                # Documento por vencer (24h)
                tipo_alerta = 'por_vencer'
                nivel_alerta = 'preventiva'
                logger.info("Creando alerta POR VENCER")
        else:
            # No necesita alerta aún
            logger.info("No necesita alerta, fecha futura")
            return
        
        logger.info(f"Creando alerta: {tipo_alerta} - {nivel_alerta}")
        transaction.on_commit(
            lambda: crear_alerta_segura(
                correspondencia_id=instance.id_correspondencia,
                usuario_id=instance.usuario.id,
                tipo_alerta=tipo_alerta,
                nivel_alerta=nivel_alerta
            )
        )
    else:
        logger.info("No tiene fecha_respuesta o usuario")
@receiver(post_save, sender=AccionCorrespondencia)
def crear_alerta_al_asignar_usuario(sender, instance, created, **kwargs):
    """Crea alerta automática cuando se asigna usuario a documento"""
    logger.info(f"Signal AccionCorrespondencia ejecutado - created: {created}")
    logger.info(f"Acción ID: {instance.id}")
    logger.info(f"Usuario destino: {instance.usuario_destino}")
    logger.info(f"Correspondencia ID: {instance.correspondencia.id_correspondencia}")
    
    # Solo cuando se crea una acción de derivación con usuario destino
    if created and instance.usuario_destino and (instance.accion or '').lower() == 'derivado':
        correspondencia = instance.correspondencia
        
        # Verificar si es una Recibida con fecha_respuesta
        if hasattr(correspondencia, 'recibida'):
            recibida = correspondencia.recibida
            logger.info(f"Es documento Recibida - Fecha respuesta: {recibida.fecha_respuesta}")
            
            if recibida.fecha_respuesta:
                hoy = timezone.now()
                logger.info(f"Hoy: {hoy}")
                
                # Evaluar fecha inmediatamente
                if recibida.fecha_respuesta <= hoy + timezone.timedelta(hours=24):
                    if recibida.fecha_respuesta <= hoy:
                        # Documento vencido
                        tipo_alerta = 'vencido'
                        nivel_alerta = 'critica'
                        logger.info("Creando alerta VENCIDO")
                    else:
                        # Documento por vencer (24h)
                        tipo_alerta = 'por_vencer'
                        nivel_alerta = 'preventiva'
                        logger.info("Creando alerta POR VENCER")
                else:
                    # No necesita alerta aún
                    logger.info("No necesita alerta, fecha futura")
                    return
                
                logger.info(f"Creando alerta: {tipo_alerta} - {nivel_alerta}")
                transaction.on_commit(
                    lambda: crear_alerta_segura(
                        correspondencia_id=correspondencia.id_correspondencia,
                        usuario_id=instance.usuario_destino.id,
                        tipo_alerta=tipo_alerta,
                        nivel_alerta=nivel_alerta
                    )
                )
            else:
                logger.info("No tiene fecha_respuesta")
        else:
            logger.info("No es documento Recibida")
           
        # Verificar si es una CorrespondenciaElaborada con fecha_seguimiento
        if hasattr(correspondencia, 'correspondenciaelaborada'):
            elaborada = correspondencia.correspondenciaelaborada
            logger.info(f"Es documento CorrespondenciaElaborada - Fecha seguimiento: {elaborada.fecha_seguimiento}")
            
            if elaborada.fecha_seguimiento:
                hoy = timezone.now()
                logger.info(f"Hoy: {hoy}")
                
                # Evaluar fecha inmediatamente
                if elaborada.fecha_seguimiento <= hoy + timezone.timedelta(hours=24):
                    if elaborada.fecha_seguimiento <= hoy:
                        # Documento vencido
                        tipo_alerta = 'vencido'
                        nivel_alerta = 'critica'
                        logger.info("Creando alerta VENCIDO")
                    else:
                        # Documento por vencer (24h)
                        tipo_alerta = 'por_vencer'
                        nivel_alerta = 'preventiva'
                        logger.info("Creando alerta POR VENCER")
                else:
                    # No necesita alerta aún
                    logger.info("No necesita alerta, fecha futura")
                    return
                
                logger.info(f"Creando alerta: {tipo_alerta} - {nivel_alerta}")
                transaction.on_commit(
                    lambda: crear_alerta_segura(
                        correspondencia_id=correspondencia.id_correspondencia,
                        usuario_id=instance.usuario_destino.id,
                        tipo_alerta=tipo_alerta,
                        nivel_alerta=nivel_alerta
                    )
                )
            else:
                logger.info("No tiene fecha_seguimiento")
        else:
            logger.info("No es documento Recibida ni CorrespondenciaElaborada")

    else:
        logger.info("No es acción de derivación con usuario destino")

@receiver(post_save, sender=Enviada)
def crear_alerta_inmediata_enviada(sender, instance, created, **kwargs):
    """Crea alerta automática inmediata al crear documento enviado"""
    logger.info(f"Signal Enviada ejecutado - created: {created}")
    logger.info(f"Documento ID: {instance.id_correspondencia}")
    logger.info(f"Fecha seguimiento: {instance.fecha_seguimiento}")
    logger.info(f"Usuario: {instance.destino_interno}")
    
    if not created:
        logger.info("No es creación, retornando...")
        return
    
    # Solo si tiene fecha_seguimiento y usuario responsable
    if instance.fecha_seguimiento and instance.destino_interno:
        hoy = timezone.now()
        logger.info(f"Hoy: {hoy}")
        
        # Evaluar fecha inmediatamente
        if instance.fecha_seguimiento <= hoy + timezone.timedelta(hours=24):
            if instance.fecha_seguimiento <= hoy:
                # Documento vencido
                tipo_alerta = 'vencido'
                nivel_alerta = 'critica'
                logger.info("Creando alerta VENCIDO")
            else:
                # Documento por vencer (24h)
                tipo_alerta = 'por_vencer'
                nivel_alerta = 'preventiva'
                logger.info("Creando alerta POR VENCER")
        else:
            # No necesita alerta aún
            logger.info("No necesita alerta, fecha futura")
            return
        
        logger.info(f"Creando alerta: {tipo_alerta} - {nivel_alerta}")
        transaction.on_commit(
            lambda: crear_alerta_segura(
                correspondencia_id=instance.id_correspondencia,
                usuario_id=instance.usuario.id,
                tipo_alerta=tipo_alerta,
                nivel_alerta=nivel_alerta
            )
        )
    else:
        logger.info("No tiene fecha_seguimiento o usuario")

@receiver(post_save, sender=CorrespondenciaElaborada)
def crear_alerta_inmediata_elaborada(sender, instance, created, **kwargs):
    """Crea alerta automática inmediata al crear documento elaborado"""
    logger.info(f"Signal Elaborada ejecutado - created: {created}")
    logger.info(f"Documento ID: {instance.id_correspondencia}")
    logger.info(f"Fecha seguimiento: {instance.fecha_seguimiento}")
    logger.info(f"Usuario: {instance.usuario.id}")
    
    if not created:
        logger.info("No es creación, retornando...")
        return
    
    # Solo si tiene fecha_seguimiento y usuario responsable
    if instance.fecha_seguimiento and instance.usuario:
        hoy = timezone.now()
        logger.info(f"Hoy: {hoy}")
            
        #Evaluar fecha inmediatamente
        if instance.fecha_seguimiento <= hoy + timezone.timedelta(hours=24):
            if instance.fecha_seguimiento <= hoy:
                # Documento vencido
                tipo_alerta = 'vencido'
                nivel_alerta = 'critica'
                logger.info("Creando alerta VENCIDO")
            else:
                # Documento por vencer (24h)
                tipo_alerta = 'por_vencer'
                nivel_alerta = 'preventiva'
                logger.info("Creando alerta POR VENCER")
        else:
            # No necesita alerta aún
            logger.info("No necesita alerta, fecha futura")
            return
            
        logger.info(f"Creando alerta: {tipo_alerta} - {nivel_alerta}")
        transaction.on_commit(
            lambda: crear_alerta_segura(
                correspondencia_id=instance.id_correspondencia,
                usuario_id=instance.usuario.id,
                tipo_alerta=tipo_alerta,
                nivel_alerta=nivel_alerta
            )
    )
    else: logger.info("No tiene fecha_seguimiento o usuario")
