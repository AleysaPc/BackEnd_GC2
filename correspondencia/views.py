from django.shortcuts import render
from .serializers import RecibidaSerializer, EnviadaSerializer, CorrespondenciaElaboradaSerializer, AccionCorrespondenciaSerializer
from rest_framework import viewsets
from .models import Correspondencia, Recibida, Enviada, CorrespondenciaElaborada, AccionCorrespondencia
from gestion_documental.mixins import PaginacionYAllDataMixin
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import generar_documento_word
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import serializers
from django.utils import timezone
from .filters import CorrespondenciaElaboradaFilter, EnviadaFilter, CorrespondenciaFilter, RecibidaFilter
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from .utils import generar_pdf_desde_html 
from rest_framework import viewsets
from .models import AccionCorrespondencia, Correspondencia
from .serializers import AccionCorrespondenciaSerializer, CorrespondenciaSerializer
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from .utils import generar_documento_word
#Para la busqueda semantica
from sentence_transformers import SentenceTransformer
from pgvector.django import CosineDistance
from django.http import FileResponse

def generar_documento(request, doc_id):
    correspondencia = get_object_or_404(CorrespondenciaElaborada, pk=doc_id)
    buffer, filename = generar_documento_word(correspondencia)
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=filename,
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

# Create your views here.
class CorrespondenciaView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    serializer_class = CorrespondenciaSerializer
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
    
    #def get_serializer_class(self):
    #    if self.action == 'list':
    #        return CorrespondenciaSerializer
    #    elif self.action == 'retrieve':
    #        return CorrespondenciaSerializer
    #    return CorrespondenciaSerializer
    
modelo = None  # Modelo global    
class RecibidaView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    serializer_class = RecibidaSerializer
    queryset = Recibida.objects.all().order_by('-fecha_registro') # Ordenar por fecha de registro en orden descendente
    
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = RecibidaFilter
    search_fields = [
        'nro_registro','referencia', 'contacto__nombre_contacto', 'contacto__apellido_pat_contacto', 'contacto__apellido_mat_contacto', 'contacto__institucion__razon_social'
    ]
    ordering_fields = ['referencia', 'contacto__nombre_contacto', 'contacto__apellido_pat_contacto', 'contacto__apellido_mat_contacto', 'contacto__institucion__razon_social']
    
    # Pasar explícitamente el contexto con request al serializer
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

   
    #Es una forma de depuración (debug) para ver qué datos y archivos
    #se están enviando al crear un nuevo documento recibido.
    def create(self, request, *args, **kwargs):
        print("✅ DATA RECIBIDA (request.data):", request.data)
        print("📎 ARCHIVOS RECIBIDOS (request.FILES):", request.FILES)

        return super().create(request, *args, **kwargs)

    #Busqueda semantica consulta del usuario    
    def get_queryset(self):
        global modelo
        queryset = super().get_queryset()

        consulta = self.request.query_params.get('consulta_semantica')
        print(f"Consulta semántica recibida: {consulta}")

        if consulta:
            if modelo is None:
                from sentence_transformers import SentenceTransformer
                modelo = SentenceTransformer('all-MiniLM-L6-v2')

            embedding = modelo.encode(consulta).tolist()

            queryset = queryset.filter(documentos__vector_embedding__isnull=False)
            queryset = queryset.annotate(similitud=CosineDistance('documentos__vector_embedding', embedding)).order_by('similitud')

        return queryset


class EnviadaView(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    serializer_class = EnviadaSerializer
    queryset = Enviada.objects.all().order_by('-fecha_registro')

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

# @csrf_exempt
#def generar_documento(request, id):
 #   if request.method == "POST":
 #       try:
 #           correspondencia = Correspondencia.objects.get(id=id)
 #           response = generar_documento_word(correspondencia)  # Llamar a la función
 #           return response  # Esto debería devolver un archivo
 #       except Correspondencia.DoesNotExist:
 #           return JsonResponse({"error": "Correspondencia no encontrada"}, status=404)
 #   return JsonResponse({"error": "Método no permitido"}, status=405)


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
        'cite', 'referencia', 'contacto__nombre_contacto', 'contacto__apellido_pat_contacto', 'contacto__apellido_mat_contacto', 'contacto__institucion__razon_social'
    ]
    ordering_fields = ['cite', 'referencia', 'contacto__nombre_contacto', 'contacto__apellido_pat_contacto', 'contacto__apellido_mat_contacto', 'contacto__institucion__razon_social']
    
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


#Derivación a varios destinatarios
User = get_user_model()
class AccionCorrespondenciaViewSet(viewsets.ModelViewSet):
    queryset = AccionCorrespondencia.objects.all()
    serializer_class = AccionCorrespondenciaSerializer

    def create(self, request, *args, **kwargs):
        print("📥 Datos recibidos en la petición:", request.data)  # Debug
        
        # Obtener los IDs de los usuarios destino (compatibilidad con 'usuario_destino' y 'usuarios')
        usuario_destino_ids = request.data.get('usuario_destino') or request.data.get('usuarios')
        print("📋 IDs de usuarios destino:", usuario_destino_ids)  # Debug

        if not usuario_destino_ids:
            return Response(
                {'error': 'Debe especificar al menos un usuario destino.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Asegurarse de que sea una lista
        if not isinstance(usuario_destino_ids, list):
            usuario_destino_ids = [usuario_destino_ids]

        acciones_creadas = []
        errores = []

        for uid in usuario_destino_ids:
            try:
                # Verificar que el usuario destino existe
                usuario_destino = User.objects.get(pk=uid)
                
                # Crear una copia de los datos para cada usuario
                data = request.data.copy()
                
                # Eliminar el campo 'usuarios' si existe, ya que no es un campo del modelo
                if 'usuarios' in data:
                    del data['usuarios']
                
                # Usar el formato correcto para el serializer
                data['usuario_destino_id'] = uid
                
                # Establecer un valor por defecto para 'accion' si no se proporciona
                if 'accion' not in data:
                    data['accion'] = 'DERIVADO'  # O el valor por defecto que prefieras
                
                # Crear el serializer con los datos
                print("📝 Datos para el serializer:", data)  # Debug
                serializer = self.get_serializer(data=data)
                
                try:
                    is_valid = serializer.is_valid()
                    if not is_valid:
                        print("❌ Errores de validación:", serializer.errors)  # Debug
                    serializer.is_valid(raise_exception=True)
                    # Guardar la acción con el usuario actual y el usuario destino
                    accion = serializer.save(usuario=request.user)
                    acciones_creadas.append(AccionCorrespondenciaSerializer(accion).data)
                except serializers.ValidationError as e:
                    errores.append({f'Error con usuario ID {uid}': str(e.detail)})
                except Exception as e:
                    errores.append({f'Error al guardar acción para usuario ID {uid}': str(e)})
                    
            except User.DoesNotExist:
                errores.append(f'Usuario destino con ID {uid} no existe.')
                continue

        # Preparar la respuesta
        if acciones_creadas:
            response_data = {'acciones': acciones_creadas}
            if errores:
                response_data['errores'] = errores
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'errores': errores if errores else ['No se pudo crear ninguna acción.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )