# services.py
from sentence_transformers import SentenceTransformer
from pgvector.django import CosineDistance
from rest_framework import serializers

modelo = None  # Variable global para el modelo

def consulta_semantica(queryset, consulta, campo_embedding='documentos__vector_embedding'):
    """
    Filtra y ordena un queryset según una consulta semántica usando SentenceTransformer.
    """
    global modelo
    if not consulta:
        return queryset

    if modelo is None:
        modelo = SentenceTransformer('all-MiniLM-L6-v2')

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
    usuario_destino_ids = request.data.get('usuario_destino') or request.data.get('usuarios')
    if not usuario_destino_ids:
        return [], [{'error': 'Debe especificar al menos un usuario destino.'}]

    if not isinstance(usuario_destino_ids, list):
        usuario_destino_ids = [usuario_destino_ids]

    acciones_creadas = []
    errores = []

    for uid in usuario_destino_ids:
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
