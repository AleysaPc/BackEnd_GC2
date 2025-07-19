from documento.models import Documento  
from django.core.exceptions import ObjectDoesNotExist

def guardar_embedding_db(nombre_documento, embedding):
    try:
        # Buscar el documento existente
        doc = Documento.objects.get(nombre_documento=nombre_documento)
        
        # Asignar embedding
        if hasattr(embedding, 'tolist'):
            doc.vector_embedding = embedding.tolist()
        else:
            doc.vector_embedding = embedding
        
        doc.save()
        print(f"Embedding guardado en DB para: {nombre_documento}")
    
    except ObjectDoesNotExist:
        print(f"Documento con nombre '{nombre_documento}' no encontrado en la base de datos.")
    except Exception as e:
        print(f"Error guardando embedding en DB: {e}")

