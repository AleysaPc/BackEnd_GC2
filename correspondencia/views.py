from django.shortcuts import render
from .serializers import CorrespondenciaListSerializer, CorrespondenciaDetailSerializer,RecibidaSerializer, EnviadaSerializer, CorrespondenciaElaboradaSerializer
from rest_framework import viewsets
from .models import Correspondencia, Recibida, Enviada, CorrespondenciaElaborada
from gestion_documental.mixins import PaginacionYAllDataMixin
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import generar_documento_word
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from .filters import CorrespondenciaElaboradaFilter, EnviadaFilter, CorrespondenciaFilter, RecibidaFilter
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

#from rest_framework.permissions import IsAuthenticated

# Create your views here.
class CorrespondenciaView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    queryset = Correspondencia.objects.all().order_by('id_correspondencia')

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = CorrespondenciaFilter
    search_fields = [
        'tipo', 'referencia'
    ]
    ordering_fields = ['tipo', 'referencia']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CorrespondenciaListSerializer
        elif self.action == 'retrieve':
            return CorrespondenciaDetailSerializer
        return CorrespondenciaListSerializer
    
    
    
    
class RecibidaView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    serializer_class = RecibidaSerializer
    queryset = Recibida.objects.all().order_by('id_correspondencia')
    
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = RecibidaFilter
    search_fields = [
        'referencia', 'contacto__nombre_contacto', 'contacto__apellido_pat_contacto', 'contacto__apellido_mat_contacto', 'contacto__institucion__razon_social'
    ]
    ordering_fields = ['referencia', 'contacto__nombre_contacto', 'contacto__apellido_pat_contacto', 'contacto__apellido_mat_contacto', 'contacto__institucion__razon_social']
    
    # Esto esta por defecto en django rest framework
    # parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        print("✅ DATA RECIBIDA (request.data):", request.data)
        print("📎 ARCHIVOS RECIBIDOS (request.FILES):", request.FILES)

        return super().create(request, *args, **kwargs)
           
    
class EnviadaView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    serializer_class = EnviadaSerializer
    queryset = Enviada.objects.all().order_by('id_correspondencia')

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = EnviadaFilter
    search_fields = [
        'cite',
    ]
    ordering_fields = ['cite']



    @action(detail=False, methods=['get'])
    def search_by_cite(self, request, cite_code):
        try:
            document = self.queryset.get(cite_code=cite_code)
            serializer = self.get_serializer(document)
            return Response(serializer.data)
        except Enviada.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        print("✅ DATA RECIBIDA (request.data):", request.data)
        print("📎 ARCHIVOS RECIBIDOS (request.FILES):", request.FILES)

        return super().create(request, *args, **kwargs)

@csrf_exempt
def generar_documento(request, id):
    if request.method == "POST":
        try:
            correspondencia = Correspondencia.objects.get(id=id)
            response = generar_documento_word(correspondencia)  # Llamar a la función
            return response  # Esto debería devolver un archivo
        except Correspondencia.DoesNotExist:
            return JsonResponse({"error": "Correspondencia no encontrada"}, status=404)
    return JsonResponse({"error": "Método no permitido"}, status=405)


from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from .utils import generar_pdf_desde_html 

class CorrespondenciaElaboradaView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    queryset = CorrespondenciaElaborada.objects.all().order_by('-fecha_registro')
    serializer_class = CorrespondenciaElaboradaSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = CorrespondenciaElaboradaFilter
    search_fields = [
        'cite',
    ]
    ordering_fields = ['cite']
    
    # Tu método existente para obtener HTML
    @action(detail=True, methods=["get"], url_path="html")
    def obtener_html(self, request, pk=None):
        try:
            correspondencia = self.get_object()
            return Response({
                "contenido_html": correspondencia.contenido_html
            })
        except CorrespondenciaElaborada.DoesNotExist:
            return Response({"error": "No encontrado"}, status=404)

    @action(detail=True, methods=["get"], url_path="pdf")
    def obtener_pdf(self, request, pk=None):
        try:
            correspondencia = self.get_object()
            html_content = correspondencia.contenido_html  # El contenido que quieres convertir

            # ✅ Generar PDF usando wkhtmltopdf
            pdf = generar_pdf_desde_html(html_content)

            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="documento_{pk}.pdf"'
            return response

        except CorrespondenciaElaborada.DoesNotExist:
            return Response({"error": "No encontrado"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

