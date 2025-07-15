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
import json
from pdfkit import from_string

#from rest_framework.permissions import IsAuthenticated

# Create your views here.
class CorrespondenciaView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    queryset = Correspondencia.objects.all().order_by('id_correspondencia')

    def get_serializer_class(self):
        if self.action == 'list':
            return CorrespondenciaListSerializer
        elif self.action == 'retrieve':
            return CorrespondenciaDetailSerializer
        return CorrespondenciaListSerializer
    
class RecibidaView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    serializer_class = RecibidaSerializer
    queryset = Recibida.objects.all().order_by('id_correspondencia')
    
    # Esto esta por defecto en django rest framework
    # parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        print("✅ DATA RECIBIDA (request.data):", request.data)
        print("📎 ARCHIVOS RECIBIDOS (request.FILES):", request.FILES)

        return super().create(request, *args, **kwargs)
        
    
class EnviadaView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    serializer_class = EnviadaSerializer
    queryset = Enviada.objects.all().order_by('id_correspondencia')

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
import io

class CorrespondenciaElaboradaView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    queryset = CorrespondenciaElaborada.objects.all().order_by('-fecha_registro')
    serializer_class = CorrespondenciaElaboradaSerializer
    
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

    # Nuevo método para obtener el PDF
    @action(detail=True, methods=["get"], url_path="pdf")
    def obtener_pdf(self, request, pk=None):
        try:
            correspondencia = self.get_object()
            
            # Aquí deberías generar el PDF desde correspondencia.contenido_html
            # Por simplicidad, solo responderemos un PDF estático o vacío
            
            # Ejemplo simple: retornar un PDF vacío (necesitarás implementar la generación real)
            #pdf_bytes = generar_pdf_desde_html(correspondencia.contenido_html)
            
            response = HttpResponse("", content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="documento_{pk}.pdf"'
            return response
        
        except CorrespondenciaElaborada.DoesNotExist:
            return Response({"error": "No encontrado"}, status=404)


#def generar_pdf_desde_html(html_content):
    # Esta función debes implementarla para convertir HTML a PDF
    # Puedes usar librerías como pdfkit, weasyprint, xhtml2pdf, etc.
    # Aquí un ejemplo muy básico con pdfkit (requiere wkhtmltopdf instalado):
    #import pdfkit
    #pdf = pdfkit.from_string(html_content, False)
    #return pdf
