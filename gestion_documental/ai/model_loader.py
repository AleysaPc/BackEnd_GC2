#Archivo responsable de cargar SBERT, singleton en memoria. 
import os

_model = None

def get_model():
    global _model

    if _model is None:
        print("🧠 Cargando modelo SBERT...")

        from sentence_transformers import SentenceTransformer

        # Railway = CPU (simplificado y estable)
        device = "cpu"

        _model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            device=device
        )

        print("✅ Modelo SBERT cargado")

    return _model