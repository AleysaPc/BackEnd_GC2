from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import action
from .serializers import DocumentoSerializer, PlantillaDocumentoSerializer
from .models import Documento, PlantillaDocumento
from gestion_documental.mixins import PaginacionYAllDataMixin

# OCR y embeddings
from PIL import Image
from documento.busquedaSemantica.ocr import extraer_texto_de_imagen, extraer_texto_de_pdf
from documento.busquedaSemantica.clean_text import limpiar_texto_ocr
from documento.busquedaSemantica.embeddings import generar_embedding

import os


class DocumentoViewSet(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    parser_classes = [MultiPartParser]

    def perform_create(self, serializer):
        documento = serializer.save()
        ruta = documento.archivo.path
        ext = os.path.splitext(ruta)[1].lower()

        if ext in ['.png', '.jpg', '.jpeg']:
            imagen = Image.open(ruta)
            texto = extraer_texto_de_imagen(imagen)
        elif ext == '.pdf':
            texto = extraer_texto_de_pdf(ruta)
        else:
            texto = ''

        texto_limpio = limpiar_texto_ocr(texto)
        embedding = generar_embedding(texto_limpio)

        if hasattr(embedding, 'tolist'):
            documento.vector_embedding = embedding.tolist()
        else:
            documento.vector_embedding = embedding

        documento.save()

from rest_framework.decorators import api_view
from rest_framework.response import Response
from sentence_transformers import SentenceTransformer
from documento.models import Documento
from pgvector.django import CosineDistance

# Modelo global para la búsqueda semántica lazy loading
modelo = None

@api_view(['POST'])
def buscar_documentos_semanticos(request):
    global modelo # Indica que usamos la variable global

    if modelo is None: # Si el modelo no ha sido cargado
        modelo = SentenceTransformer('all-MiniLM-L6-v2')
    # Fin del lazy loading
    consulta = request.data.get('consulta', '')
    if not consulta:
        return Response({'error': 'Consulta no proporcionada'}, status=400)

    # Generar el embedding de la consulta
    embedding_consulta = modelo.encode(consulta).tolist()

    # Buscar los documentos más similares por similitud coseno
    documentos = (
        Documento.objects
        .annotate(similitud=CosineDistance('vector_embedding', embedding_consulta))
        .order_by('similitud')[:5]  # menor distancia = mayor similitud
    )

    data = []
    for doc in documentos:
        if doc.similitud is None:
            continue  # Excluir documentos sin similitud

        data.append({
            'id': doc.pk,
            'nombre_documento': doc.nombre_documento,
            'texto_plano': doc.contenido_extraido[:200] if doc.contenido_extraido else '',
            'similitud': round(1 - doc.similitud, 4),  # 1 - distancia coseno = similitud
        })

    print("DOC:", doc)
    print("ID:", getattr(doc, 'pk', None))  # Debug

    return Response(data)


class PlantillaDocumentoViewSet(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    queryset = PlantillaDocumento.objects.all()
    serializer_class = PlantillaDocumentoSerializer
