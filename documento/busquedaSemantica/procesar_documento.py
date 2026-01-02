import os
import django
from PIL import Image
import sys
#################ELIMINAR ARCHIVO
# 1. Inicializar entorno Django para usar modelos y ORM
# Añadir la ruta del proyecto al sys.path para que Django lo encuentre
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(project_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_documental.settings")
try:
    django.setup()
except Exception as e:
    print("Error al configurar Django:", e)
    print("Python path:", sys.path)
    raise

# 2. Importar funciones y modelos ahora que Django está listo
from ocr import extraer_texto_de_imagen, extraer_texto_de_pdf
from clean_text import limpiar_texto_ocr
from embeddings import generar_embedding
from documento.models import Documento

# 3. Función para guardar embedding usando ORM
def guardar_embedding_db(nombre_documento, embedding):
    try:
        doc = Documento.objects.get(nombre_documento=nombre_documento)
        doc.vector_embedding = embedding.tolist()  # Asegúrate que embedding es numpy array o lista
        doc.save()
        print(f"Embedding guardado en DB para: {nombre_documento}")
    except Exception as e:
        print(f"Error guardando embedding: {e}")

# 4. Función para procesar un documento
def procesar_documento(nombre_documento, ruta_archivo):
    ext = os.path.splitext(ruta_archivo)[1].lower()
    if ext in ['.png', '.jpg', '.jpeg']:
        imagen = Image.open(ruta_archivo)
        texto_extraido = extraer_texto_de_imagen(imagen)
    elif ext == '.pdf':
        texto_extraido = extraer_texto_de_pdf(ruta_archivo)
    else:
        print(f"Formato no soportado para OCR: {ext}")
        return

    texto_limpio = limpiar_texto_ocr(texto_extraido)
    embedding = generar_embedding(texto_limpio)

    print(f"Embedding generado para {nombre_documento}")
    guardar_embedding_db(nombre_documento, embedding)

# 5. Función principal que recorre la carpeta y procesa documentos
def main():
    # Subir tres niveles desde el directorio actual para llegar a la raíz del proyecto
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    carpeta_documentos = os.path.join(base_dir, "media", "documentos")
    print(f"Buscando documentos en: {carpeta_documentos}")

    if not os.path.exists(carpeta_documentos):
        print(f"Error: La carpeta '{carpeta_documentos}' no existe.")
        return
    
    # Contador de archivos encontrados
    archivos_encontrados = 0
    
    for root, dirs, files in os.walk(carpeta_documentos):
        for nombre_archivo in files:
            if nombre_archivo.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
                ruta_completa = os.path.join(root, nombre_archivo)
                print(f"Procesando: {ruta_completa}")
                archivos_encontrados += 1
                procesar_documento(nombre_archivo, ruta_completa)
            else:
                print(f"Archivo ignorado (extensión no soportada): {nombre_archivo}")
                
    if archivos_encontrados == 0:
        print("No se encontraron archivos para procesar (buscando .png, .jpg, .jpeg, .pdf)")
    else:
        print(f"Total de archivos encontrados: {archivos_encontrados}")

if __name__ == "__main__":
    main()
