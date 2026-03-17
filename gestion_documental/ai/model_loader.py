_model = None

def get_model():
    global _model
    if _model is None:
        print("🧠 Cargando modelo SBERT...")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("Necesitas instalar sentence-transformers para ejecutar esta tarea.")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Modelo cargado correctamente.")
    return _model