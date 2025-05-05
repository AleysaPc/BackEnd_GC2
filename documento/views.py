from rest_framework import viewsets
from .serializers import TipoDocumentoSerializer, DocumentoSerializer
from .models import TipoDocumento, Documento
from gestion_documental.mixins import PaginacionYAllDataMixin
# Create your views here.
# Tambien va la paginacion

class TipoDocumentoViewSet(PaginacionYAllDataMixin,viewsets.ModelViewSet):
    queryset = TipoDocumento.objects.all()
    serializer_class = TipoDocumentoSerializer

class DocumentoViewSet(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer