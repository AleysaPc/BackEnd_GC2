#Este archivo es un módulo de servicios en Django. Es decir aquí se
#concentra la lógica de negocio separado de los modelos y vistas.

import logging #Permite registrar eventos (debug, info, errores).
from django.db import IntegrityError, transaction #Error de base de datos  Ej. ALerta duplicada
from django.utils import timezone #Permite trabajar con fechas y horas.
from .models import AlertaVencimiento #Modelo de la base de datos.

logger = logging.getLogger(__name__) #Permite registrar eventos (debug, info, errores).

#Función principal 
def crear_alerta_segura(correspondencia_id, usuario_id, tipo_alerta, nivel_alerta='informativa'):
    """Crea alerta con manejo de concurrencia y logging estructurado"""
    try:
        # ✅ Debug para desarrollo, no para producción
        logger.debug(
            "Iniciando creación de alerta",
            extra={
                "correspondencia_id": correspondencia_id,
                "usuario_id": usuario_id,
                "tipo_alerta": tipo_alerta,
                "nivel_alerta": nivel_alerta
            }
        )
        
        # ✅ atomic() solo para consistencia, no previene IntegrityError
        #Esto garantiza que todo se ejecute como una sola operación
        with transaction.atomic():
                                               #Busca si ya existe si no existe lo crea get o create                                 
            alerta, created = AlertaVencimiento.objects.get_or_create(
                #Campos de búsqueda coincide con UniqueConstraint
                correspondencia_id=correspondencia_id,
                usuario_responsable_id=usuario_id,
                tipo_alerta=tipo_alerta,
                defaults={
                    'nivel_alerta': nivel_alerta,
                    'vista': False
                }
            )
            
            # ✅ Re-alerta: reactivar si ya existía
            if not created:
                alerta.fecha_alerta = timezone.now()
                alerta.vista = False  # vuelve a notificar
                alerta.fecha_vista = None # limpia fecha al reactivar
                alerta.save(update_fields=['fecha_alerta', 'vista', 'fecha_vista'])
                reactivada = True
            else:
                reactivada = False
        
        # ✅ Info solo para eventos importantes
        logger.info(
            "Alerta procesada",
            extra={
                "alerta_id": alerta.id if alerta else None,
                "creada": created,
                "reactivada": reactivada,
                "correspondencia_id": correspondencia_id,
                "usuario_id": usuario_id,
                "tipo_alerta": tipo_alerta
            }
        )
        
        # ✅ Retorno expresivo
        return {
            "alerta": alerta,
            "creada": created,
            "reactivada": reactivada
        }
        
    except IntegrityError as e:
        # ✅ Captura específica de concurrencia
        logger.warning(
            "Alerta duplicada por concurrencia",
            extra={
                "error": str(e),
                "correspondencia_id": correspondencia_id,
                "usuario_id": usuario_id,
                "tipo_alerta": tipo_alerta
            }
        )
        
        # Intentar obtener la existente
        try:
            alerta = AlertaVencimiento.objects.get(
                correspondencia_id=correspondencia_id,
                usuario_responsable_id=usuario_id,
                tipo_alerta=tipo_alerta
            )
            return {
                "alerta": alerta,
                "creada": False,
                "reactivada": False
            }
        except AlertaVencimiento.DoesNotExist:
            logger.error(
                "Error inesperado al obtener alerta existente",
                extra={"error": str(e), "correspondencia_id": correspondencia_id}
            )
            return {
                "alerta": None,
                "creada": False,
                "reactivada": False
            }
        
    except Exception as e:
        logger.error(
            "Error crítico en crear_alerta_segura",
            extra={
                "error": str(e),
                "correspondencia_id": correspondencia_id,
                "usuario_id": usuario_id,
                "tipo_alerta": tipo_alerta
            },
            exc_info=True
        )
        return {
            "alerta": None,
            "creada": False,
            "reactivada": False
        }

#Segunda función
def alertas_usuario(usuario_id): #Devuelve alertas no vistas de un usuario
    """Obtiene alertas no vistas de un usuario"""
    try:
        logger.debug(
            "Obteniendo alertas de usuario",
            extra={"usuario_id": usuario_id}
        )
        #Query means Consulta
        alertas = AlertaVencimiento.objects.filter(
            usuario_responsable_id=usuario_id,
            vista=False   #Las alertas vistas ya no aparecerán
        ).order_by('-fecha_alerta')
        
        logger.info(
            "Alertas obtenidas",
            extra={
                "usuario_id": usuario_id,
                "cantidad": alertas.count()
            }
        )
        
        return alertas
        
    except Exception as e:
        logger.error(
            "Error obteniendo alertas de usuario",
            extra={
                "error": str(e),
                "usuario_id": usuario_id
            },
            exc_info=True
        )
        return AlertaVencimiento.objects.none()

#Este archivo maneja la lógica de negocio de alertas: evita 
# duplicados mediante control de concurrencia y restricciones, 
# crea o reactiva alertas de forma segura, y permite obtener las
#  alertas no vistas de un usuario.