import os
import torch

_model = None

def get_model():
    # 🚫 Desactivar SBERT temporalmente
    if os.getenv("DISABLE_SBERT", "false") == "true":
        print("🚫 SBERT desactivado")
        return None

    global _model
    if _model is None:
        print("🧠 Cargando modelo SBERT...")
        from sentence_transformers import SentenceTransformer

        device = 'cpu'  # fuerza CPU en Railway

        _model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            device=device
        )
        print(f"✅ Modelo cargado en {device}")

    return _model