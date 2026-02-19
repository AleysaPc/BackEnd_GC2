# services.py
import logging
from pgvector.django import CosineDistance
from rest_framework import serializers

modelo = None  # Variable global para el modelo
logger = logging.getLogger(__name__)

def consulta_semantica(queryset, consulta, campo_embedding='documentos__vector_embedding'):
    """
    Filtra y ordena un queryset según una consulta semántica usando SentenceTransformer.
    """
    global modelo
    if not consulta:
        return queryset

    if modelo is None:
        try:
            from sentence_transformers import SentenceTransformer
            modelo = SentenceTransformer('all-MiniLM-L6-v2') #Modelo SBERT version 2
        except Exception as exc:
            logger.warning("Búsqueda semántica deshabilitada en este servicio: %s", exc)
            return queryset

    embedding = modelo.encode(consulta).tolist()

    queryset = queryset.filter(**{f"{campo_embedding}__isnull": False})
    queryset = queryset.annotate(similitud=CosineDistance(campo_embedding, embedding)).order_by('similitud')
    return queryset

def crear_objetos_multiple(serializer_class, request, usuario=None, extra_fields=None):
    """
    Crea objetos para cada usuario destino si es necesario.
    `extra_fields` es un dict con datos adicionales que quieres inyectar.
    """
    extra_fields = extra_fields or {}
    usuario_destino_id = request.data.get('usuario_destino') or request.data.get('usuarios')
    if not usuario_destino_id:
        return [], [{'error': 'Debe especificar al menos un usuario destino.'}]

    if not isinstance(usuario_destino_id, list):
        usuario_destino_id = [usuario_destino_id]

    acciones_creadas = []
    errores = []

    for uid in usuario_destino_id:
        data = request.data.copy()
        data.update(extra_fields)
        data['usuario_destino_id'] = uid

        serializer = serializer_class(data=data)
        try:
            serializer.is_valid(raise_exception=True)
            obj = serializer.save(usuario=usuario)
            acciones_creadas.append(serializer_class(obj).data)
        except serializers.ValidationError as e:
            errores.append({f'Error con usuario ID {uid}': str(e.detail)})
        except Exception as e:
            errores.append({f'Error al guardar acción para usuario ID {uid}': str(e)})

    return acciones_creadas, errores
