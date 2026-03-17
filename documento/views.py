# views.py
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view
from pgvector.django import CosineDistance

from .serializers import DocumentoSerializer, PlantillaDocumentoSerializer
from .models import Documento, PlantillaDocumento
from gestion_documental.mixins import PaginacionYAllDataMixin
from gestion_documental.ai.model_loader import get_model  # <-- nuestro singleton SBERT

# -------------------------------
# ViewSet para Documentos
# -------------------------------
class DocumentoViewSet(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    parser_classes = [MultiPartParser]

    def perform_create(self, serializer):
        documento = serializer.save()
        # Usar la versión asíncrona para procesamiento pesado
        from documento.busquedaSemantica.procesar_documento import procesar_documento
        procesar_documento(documento.nombre_documento, documento.archivo.path)


# -------------------------------
# ViewSet para Plantillas
# -------------------------------
class PlantillaDocumentoViewSet(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    queryset = PlantillaDocumento.objects.all()
    serializer_class = PlantillaDocumentoSerializer


# -------------------------------
# API para búsqueda semántica
# -------------------------------
@api_view(['POST'])
def buscar_documentos_semanticos(request):
    consulta = request.data.get('consulta', '')
    if not consulta:
        return Response({'error': 'Consulta no proporcionada'}, status=400)

    try:
        modelo = get_model()  # Reutiliza la instancia única de SBERT
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

    except Exception as e:
        return Response({'error': f'Error en búsqueda semántica: {str(e)}'}, status=500)