from django.shortcuts import render
from .serializers import CorrespondenciaListSerializer, CorrespondenciaDetailSerializer, RecibidaSerializer, EnviadaSerializer, InternaSerializer
from rest_framework import viewsets
from .models import Correspondencia, Recibida, Enviada, Interna
from gestion_documental.mixins import PaginacionYAllDataMixin
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import generar_documento_word
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

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
    parser_classes = (MultiPartParser, FormParser)

class EnviadaView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    serializer_class = EnviadaSerializer
    queryset = Enviada.objects.all().order_by('id_correspondencia')

class InternaView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    serializer_class = InternaSerializer
    queryset = Interna.objects.all().order_by('id_correspondencia')

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