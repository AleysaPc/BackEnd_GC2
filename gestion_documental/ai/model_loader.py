import os
import torch

_model = None  # ← Esta línea falta

def get_model():
    global _model
    if _model is None:
        print("🧠 Cargando modelo SBERT...")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("Necesitas instalar sentence-transformers para ejecutar esta tarea.")
        
        # Configuración para Railway
        device = 'cuda' if (torch.cuda.is_available() and os.getenv('RAILWAY_ENVIRONMENT') == 'production') else 'cpu'
        
        # Optimización para memoria limitada
        _model = SentenceTransformer(
            "all-MiniLM-L6-v2", 
            device=device,
            model_kwargs={'torch_dtype': torch.float16 if device == 'cuda' else torch.float32}
        )
        print(f"✅ Modelo cargado en {device} (Railway)")
    return _model