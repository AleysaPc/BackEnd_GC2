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


class PlantillaDocumentoViewSet(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    queryset = PlantillaDocumento.objects.all()
    serializer_class = PlantillaDocumentoSerializer
