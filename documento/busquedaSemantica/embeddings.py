from gestion_documental.ai.model_loader import get_model  # nuestro singleton SBERT

def generar_embedding(texto: str) -> list[float]:
    """
    Genera un embedding para un texto usando el modelo SBERT único.
    """
    modelo = get_model()
    return modelo.encode(texto).tolist()