import redis
import tempfile
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def get_redis_client():
    """Obtener cliente Redis configurado para Railway"""
    redis_url = settings.REDIS_URL
    logger.info(f"Conectando a Redis: {redis_url}")
    return redis.from_url(redis_url, decode_responses=False)

def guardar_archivo_redis(archivo, key):
    """Guardar archivo en Redis"""
    try:
        client = get_redis_client()
        archivo.seek(0)
        contenido = archivo.read()
        
        # Guardar en Redis con TTL de 1 hora
        client.set(key, contenido)
        client.expire(key, 3600)
        
        logger.info(f"✅ Archivo guardado en Redis: {key} (tamaño: {len(contenido)} bytes)")
        return key
        
    except Exception as e:
        logger.error(f"❌ Error guardando archivo en Redis: {str(e)}")
        raise

def obtener_archivo_redis(key):
    """Obtener archivo desde Redis"""
    try:
        client = get_redis_client()
        contenido = client.get(key)
        
        if not contenido:
            logger.error(f"❌ Archivo no encontrado en Redis: {key}")
            return None
        
        # Crear archivo temporal
        ext = os.path.splitext(key)[1].lower() or '.pdf'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        temp_file.write(contenido)
        temp_file.close()
        
        logger.info(f"✅ Archivo temporal creado desde Redis: {temp_file.name}")
        return temp_file.name
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo archivo desde Redis: {str(e)}")
        return None

def limpiar_archivo_temporal(ruta_temporal):
    """Eliminar archivo temporal"""
    try:
        os.unlink(ruta_temporal)
        logger.info(f"🧹 Archivo temporal eliminado: {ruta_temporal}")
    except Exception as e:
        logger.warning(f"⚠️ Error eliminando archivo temporal: {str(e)}")