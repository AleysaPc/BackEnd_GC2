from sentence_transformers import SentenceTransformer

# Cargar el modelo preentrenado de Sentence Transformers
modelo = SentenceTransformer('all-MiniLM-L6-v2')

def generar_embedding(texto):
    """Genera el embedding para un texto dado."""
    return modelo.encode(texto)
