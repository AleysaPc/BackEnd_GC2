import os
import torch

_model = None

def get_model(): #Solo carga el modelo
    global _model
    if _model is None:
        print("🧠 Cargando modelo SBERT...")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("Necesitas instalar sentence-transformers: pip install sentence-transformers")
        
        # 🔥 Detección automática de entorno
        railway_env = os.getenv('RAILWAY_ENVIRONMENT', '') != ''
        
        if railway_env:
            # Configuración para Railway (producción)
            device = 'cpu'  # Railway no tiene GPU
            max_seq = 256    # Reducir para ahorrar memoria
            print("🚂 Entorno Railway detectado - usando configuración optimizada")
        else:
            # Configuración para desarrollo local
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            max_seq = 512    # Máximo rendimiento local
            print("💻 Entorno local detectado - usando configuración completa")
        
        print(f"🔧 Usando dispositivo: {device}")
        
        try:
            # Cargar modelo primero sin especificar dispositivo
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            
            # Mover al dispositivo DESPUÉS de la carga completa
            _model = _model.to(device)
            
            # 🔥 Configuración específica por entorno
            _model.max_seq_length = max_seq
            print(f"⚙️ max_seq_length configurado a: {max_seq}")
            
            # Pre-calentar modelo (opcional pero recomendado)
            if not railway_env:
                _model.encode("test")  # Solo en local para pre-calentamiento
            
            print(f"✅ Modelo cargado exitosamente en {device}")
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")
            raise
            
    return _model