from gestion_documental.ai.model_loader import get_model
from pgvector.django import CosineDistance

def get_semantic_queryset(
    queryset, 
    consulta, 
    embedding_field='documentos__vector_embedding',
    similarity_threshold=0.5,
    limit=None
):
    """
    Filtra un queryset usando búsqueda semántica.
    
    Args:
        queryset: Queryset de Django a filtrar
        consulta (str): Texto de búsqueda
        embedding_field (str): Campo que contiene el embedding (por defecto: 'documentos__vector_embedding')
        similarity_threshold (float): Umbral mínimo de similitud (0-1)
        limit (int, optional): Número máximo de resultados a devolver
        
    Returns:
        QuerySet: Queryset filtrado y ordenado por similitud descendente
    """
    
    if not consulta or not consulta.strip():
        return queryset.none()
    
    try:
        # Generar embedding para la consulta
        model = get_model()
        embedding = model.encode(consulta).tolist()
        
        # Aplicar búsqueda semántica
        queryset = queryset.annotate(
            similitud=1.0 - CosineDistance(embedding_field, embedding)
        ).filter(
            similitud__gte=similarity_threshold,
            **{f"{embedding_field}__isnull": False}
        ).order_by('-similitud')
        
        # Aplicar límite si se especifica
        if limit is not None:
            queryset = queryset[:int(limit)]
            
        return queryset
        
    except Exception as e:
        # En producción, considera usar logging en lugar de print
        print(f"Error en búsqueda semántica: {str(e)}")
        return queryset.none()
