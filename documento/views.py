from rest_framework import viewsets
from .serializers import DocumentoSerializer, PlantillaDocumentoSerializer
from .models import Documento, PlantillaDocumento
from gestion_documental.mixins import PaginacionYAllDataMixin
from rest_framework.parsers import MultiPartParser
# Create your views here.
# Tambien va la paginacion

class DocumentoViewSet(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    parser_classes = [MultiPartParser]

# views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Documento
from .serializers import DocumentoSerializer

@api_view(['POST'])
def upload_documento(request):
    if request.method == 'POST':
        archivo = request.FILES.get('archivo')
        nombre_documento = request.data.get('nombre_documento')
        tipo_documento = request.data.get('id_tipo_documento')
        id_correspondencia = request.data.get('id_correspondencia')

        if not archivo or not nombre_documento or not tipo_documento or not id_correspondencia:
            return Response({"error": "Faltan datos necesarios"}, status=status.HTTP_400_BAD_REQUEST)

        # Aquí puedes guardar el documento en la base de datos
        documento = Documento.objects.create(
            archivo=archivo,
            nombre_documento=nombre_documento,
            tipo_documento_id=tipo_documento,
            correspondencia_id=id_correspondencia
        )

        return Response(DocumentoSerializer(documento).data, status=status.HTTP_201_CREATED)

class PlantillaDocumentoViewSet(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    queryset = PlantillaDocumento.objects.all()
    serializer_class = PlantillaDocumentoSerializer