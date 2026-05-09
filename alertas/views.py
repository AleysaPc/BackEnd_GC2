# alertas/views.py
import logging #Registro de eventos (debug, errores, etc)
from rest_framework import status # códigos HTTP (200, 201, 404, etc)
from rest_framework.decorators import api_view, permission_classes
                                #api_view - Convierte funciones en endpoints API
                                #permission_classes - define permisos
                                #isAuthenticated - Verifica que el usuario esté autenticado
from rest_framework.permissions import IsAuthenticated 
from rest_framework.response import Response
from django.db.models import Count #función de agregación en base de datos
from .models import AlertaVencimiento #Modelo
from .services import crear_alerta_segura, alertas_usuario #Funciones logica de negocio separada

logger = logging.getLogger(__name__)

#Función auxiliar
def get_color_por_tipo(tipo_alerta, vista):
    """Función auxiliar para obtener color sin crear objeto"""
    if vista:
        return '🟢'
    return {
        'por_vencer': '🟡',
        'vencido': '🔴',
    }.get(tipo_alerta, '⚪')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_alertas_usuario(request):
    """Obtener alertas no vistas del usuario actual"""
    try:
        logger.debug(
            "Obteniendo alertas del usuario",
            extra={"usuario_id": request.user.id}
        )
        #Obtener alertas
        alertas = alertas_usuario(request.user.id).select_related('correspondencia')
        
        data = []
        for alerta in alertas: #Construcción manual del Json
            nro_registro = None
            if hasattr(alerta.correspondencia, "recibida"):
                nro_registro = alerta.correspondencia.recibida.nro_registro
            data.append({
                'id': alerta.id,
                'correspondencia_id': alerta.correspondencia.id_correspondencia,
                'correspondencia_codigo': alerta.correspondencia.referencia,
                'nro_registro': nro_registro,
                'tipo_alerta': alerta.tipo_alerta,
                'nivel_alerta': alerta.nivel_alerta,
                'fecha_alerta': alerta.fecha_alerta,
                'vista': alerta.vista,
                'fecha_vista': alerta.fecha_vista,
                'color_estado': get_color_por_tipo(alerta.tipo_alerta, alerta.vista)  # ✅ Sin crear objeto
            })
        
        logger.info(
            "Alertas del usuario obtenidas",
            extra={
                "usuario_id": request.user.id,
                "cantidad": len(data)
            }
        )
        
        return Response(data, status=status.HTTP_200_OK)
    #Manejo de errores   
    except Exception as e:
        logger.error(
            "Error obteniendo alertas del usuario",
            extra={
                "error": str(e),
                "usuario_id": request.user.id
            },
            exc_info=True
        )
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_alerta_manual(request):
    """Crear alerta manualmente"""
    try:
        data = request.data
        correspondencia_id = data.get('correspondencia_id')
        tipo_alerta = data.get('tipo_alerta')
        nivel_alerta = data.get('nivel_alerta', 'informativa')
        
        # ✅ Logging seguro sin datos sensibles
        logger.debug(
            "Datos recibidos para crear alerta",
            extra={
                "correspondencia_id": correspondencia_id,
                "tipo_alerta": tipo_alerta,
                "nivel_alerta": nivel_alerta
            }
        )
        
        # ✅ Seguridad: solo puede crear para sí mismo
        usuario_id = request.user.id
        
        resultado = crear_alerta_segura(
            correspondencia_id=correspondencia_id,
            usuario_id=usuario_id,
            tipo_alerta=tipo_alerta,
            nivel_alerta=nivel_alerta
        )
        
        logger.info(
            "Resultado de creación de alerta",
            extra={
                "alerta_id": resultado["alerta"].id if resultado["alerta"] else None,
                "creada": resultado["creada"],
                "reactivada": resultado["reactivada"]
            }
        )
        
        if resultado["alerta"]:
            message = "Alerta creada exitosamente" if resultado["creada"] else "Alerta reactivada"
            # ✅ HTTP status correcto
            status_code = status.HTTP_201_CREATED if resultado["creada"] else status.HTTP_200_OK
            
            return Response({
                'message': message,
                'alerta_id': resultado["alerta"].id,
                'creada': resultado["creada"],
                'reactivada': resultado["reactivada"],
                'tipo_alerta': resultado["alerta"].tipo_alerta,
                'color_estado': get_color_por_tipo(resultado["alerta"].tipo_alerta, False)
            }, status=status_code)
        else:
            return Response(
                {'error': 'No se pudo crear la alerta'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(
            "Error creando alerta manual",
            extra={
                "error": str(e),
                "usuario_id": request.user.id
            },
            exc_info=True
        )
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_alerta_vista(request, alerta_id):
    """Marcar alerta como vista"""
    try:
        logger.debug(
            "Marcando alerta como vista",
            extra={
                "alerta_id": alerta_id,
                "usuario_id": request.user.id
            }
        )
        #Busca la alerta
        alerta = AlertaVencimiento.objects.get(
            id=alerta_id, 
            usuario_responsable=request.user
        )
        #Marca la alerta como vista
        alerta.marcar_como_vista()
        
        logger.info(
            "Alerta marcada como vista",
            extra={
                "alerta_id": alerta_id,
                "usuario_id": request.user.id
            }
        )
        
        return Response({'message': 'Alerta marcada como vista'}, status=status.HTTP_200_OK)
        
    except AlertaVencimiento.DoesNotExist:
        logger.warning(
            "Alerta no encontrada para marcar como vista",
            extra={
                "alerta_id": alerta_id,
                "usuario_id": request.user.id
            }
        )
        return Response(
            {'error': 'Alerta no encontrada'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(
            "Error marcando alerta como vista",
            extra={
                "error": str(e),
                "alerta_id": alerta_id,
                "usuario_id": request.user.id
            },
            exc_info=True
        )
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estadisticas_alertas(request):
    """Obtener estadísticas de alertas del usuario"""
    try:
        logger.debug(
            "Obteniendo estadísticas de alertas",
            extra={"usuario_id": request.user.id}
        )
        
        # ✅ Optimización: una sola query con annotate()
        alertas_por_tipo = (
            AlertaVencimiento.objects
            .filter(usuario_responsable=request.user, vista=False)
            .values('tipo_alerta')
            .annotate(cantidad=Count('id'))
        )
        
        # Convertir a formato esperado
        tipo_stats = {}
        for item in alertas_por_tipo:
            tipo = item['tipo_alerta']
            tipo_stats[tipo] = {
                'cantidad': item['cantidad'],
                'color': get_color_por_tipo(tipo, False)
            }
        
        # Total de alertas no vistas
        total_no_vistas = sum(item['cantidad'] for item in alertas_por_tipo)
        
        # Alertas por nivel (optimizado)
        alertas_por_nivel = (
            AlertaVencimiento.objects
            .filter(usuario_responsable=request.user, vista=False)
            .values('nivel_alerta')
            .annotate(cantidad=Count('id'))
        )
        
        nivel_stats = {item['nivel_alerta']: item['cantidad'] for item in alertas_por_nivel}
        
        logger.info(
            "Estadísticas de alertas obtenidas",
            extra={
                "usuario_id": request.user.id,
                "total_no_vistas": total_no_vistas
            }
        )
        
        return Response({
            'total_no_vistas': total_no_vistas,
            'alertas_por_tipo': tipo_stats,
            'alertas_por_nivel': nivel_stats
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(
            "Error obteniendo estadísticas de alertas",
            extra={
                "error": str(e),
                "usuario_id": request.user.id
            },
            exc_info=True
        )
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )