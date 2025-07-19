from sentence_transformers import SentenceTransformer

# Cargamos el modelo preentrenado
modelo = SentenceTransformer('all-MiniLM-L6-v2')

def generar_embedding(texto):
    embedding = modelo.encode(texto)
    return embedding
