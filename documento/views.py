from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import action
from .serializers import DocumentoSerializer, PlantillaDocumentoSerializer
from .models import Documento, PlantillaDocumento
from gestion_documental.mixins import PaginacionYAllDataMixin

# OCR y embeddings
from PIL import Image
from documento.tasks import ocr_task, limpiar_task, embeddings_task, guardar_task
from celery import chain

import os


class DocumentoViewSet(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    parser_classes = [MultiPartParser]

    def perform_create(self, serializer):
        documento = serializer.save()
        # Usar la versión asíncrona
        from documento.busquedaSemantica.procesar_documento import procesar_documento
        procesar_documento(documento.nombre_documento, documento.archivo.path)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from sentence_transformers import SentenceTransformer
from documento.models import Documento
from pgvector.django import CosineDistance

# Modelo global para la búsqueda semántica lazy loading
modelo = None

@api_view(['POST'])
def buscar_documentos_semanticos(request):
    consulta = request.data.get('consulta', '')
    if not consulta:
        return Response({'error': 'Consulta no proporcionada'}, status=400)

    global modelo
    if modelo is None:
        modelo = SentenceTransformer('all-MiniLM-L6-v2')

    embedding_consulta = modelo.encode(consulta).tolist()

    documentos = (
        Documento.objects
        .annotate(similitud=CosineDistance('vector_embedding', embedding_consulta))
        .order_by('similitud')[:5]
    )

    data = []
    for doc in documentos:
        if doc.similitud is None:
            continue
        data.append({
            'id': doc.pk,
            'nombre_documento': doc.nombre_documento,
            'texto_plano': doc.contenido_extraido[:200] if doc.contenido_extraido else '',
            'similitud': round(1 - doc.similitud, 4),
        })

    return Response(data)


class PlantillaDocumentoViewSet(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    queryset = PlantillaDocumento.objects.all()
    serializer_class = PlantillaDocumentoSerializer
