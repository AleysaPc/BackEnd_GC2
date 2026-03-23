import os
import torch

_model = None

def get_model():
    global _model
    if _model is None:
        print("🧠 Cargando modelo SBERT...")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("Necesitas instalar sentence-transformers: pip install sentence-transformers")
        
        # Configuración mejorada para desarrollo local
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"🔧 Usando dispositivo: {device}")
        
        try:
            # Carga más robusta
            _model = SentenceTransformer(
                "all-MiniLM-L6-v2", 
                device=device
            )
            print(f"✅ Modelo cargado exitosamente en {device}")
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")
            raise
            
    return _model