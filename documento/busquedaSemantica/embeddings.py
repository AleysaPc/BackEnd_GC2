from sentence_transformers import SentenceTransformer

modelo = SentenceTransformer('all-MiniLM-L6-v2')

def generar_embedding(texto):
    return modelo.encode(texto)
