from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse, FileResponse
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend

from .models import Correspondencia, Recibida, Enviada, CorrespondenciaElaborada, AccionCorrespondencia, HistorialVisualizacion
from .serializers import (
    CorrespondenciaSerializer, RecibidaSerializer, EnviadaSerializer, 
    CorrespondenciaElaboradaSerializer, AccionCorrespondenciaSerializer
)
from .filters import CorrespondenciaFilter, RecibidaFilter, EnviadaFilter, CorrespondenciaElaboradaFilter
from gestion_documental.mixins import PaginacionYAllDataMixin
from .utils import generar_documento_word, generar_pdf_desde_html
from .services.services import consulta_semantica, crear_objetos_multiple

User = get_user_model()


# ===========================
# Clase base para ViewSets
# ===========================
class BaseViewSet(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    """
    Clase base para reducir duplicación:
    - Filtros y ordering
    - Búsqueda semántica
    - get_serializer_context
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = None
    search_fields = []
    ordering_fields = []

    semantic_search_field = 'documentos__vector_embedding'

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        consulta = self.request.query_params.get('consulta_semantica')
        return consulta_semantica(queryset, consulta, self.semantic_search_field)


# ===========================
# Documentos Word
# ===========================
def generar_documento(request, doc_id):
    correspondencia = get_object_or_404(CorrespondenciaElaborada, pk=doc_id)
    buffer, filename = generar_documento_word(correspondencia)
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=filename,
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


# ===========================
# ViewSets
# ===========================
class CorrespondenciaView(BaseViewSet):
    serializer_class = CorrespondenciaSerializer
    queryset = Correspondencia.objects.all().order_by('id_correspondencia')
    filterset_class = CorrespondenciaFilter
    search_fields = ['tipo', 'referencia', 'contacto__institucion__razon_social']
    ordering_fields = ['tipo', 'referencia']


class RecibidaView(BaseViewSet):
    serializer_class = RecibidaSerializer
    queryset = Recibida.objects.all().order_by('-fecha_registro')
    filterset_class = RecibidaFilter
    search_fields = [
        'nro_registro','referencia','contacto__nombre_contacto',
        'contacto__apellido_pat_contacto','contacto__apellido_mat_contacto',
        'contacto__institucion__razon_social'
    ]
    ordering_fields = search_fields

    def create(self, request, *args, **kwargs):
        print("✅ DATA RECIBIDA (request.data):", request.data)
        print("📎 ARCHIVOS RECIBIDOS (request.FILES):", request.FILES)
        return super().create(request, *args, **kwargs)


class EnviadaView(BaseViewSet):
    serializer_class = EnviadaSerializer
    queryset = Enviada.objects.all().order_by('-fecha_registro')
    filterset_class = EnviadaFilter
    search_fields = ['cite']
    ordering_fields = ['cite']

    def create(self, request, *args, **kwargs):
        print("✅ DATA RECIBIDA (request.data):", request.data)
        print("📎 ARCHIVOS RECIBIDOS (request.FILES):", request.FILES)
        return super().create(request, *args, **kwargs)


class CorrespondenciaElaboradaView(BaseViewSet):
    queryset = CorrespondenciaElaborada.objects.all().order_by('-fecha_registro')
    serializer_class = CorrespondenciaElaboradaSerializer
    filterset_class = CorrespondenciaElaboradaFilter
    search_fields = [
        'cite', 'referencia','contacto__nombre_contacto','contacto__apellido_pat_contacto',
        'contacto__apellido_mat_contacto','contacto__institucion__razon_social',
        'plantilla__nombre_plantilla','email'
    ]
    ordering_fields = search_fields

    @action(detail=True, methods=["get"], url_path="html")
    def obtener_html(self, request, pk=None):
        correspondencia = self.get_object()
        return Response({"contenido_html": correspondencia.contenido_html})

    @action(detail=True, methods=["get"], url_path="pdf")
    def obtener_pdf(self, request, pk=None):
        correspondencia = self.get_object()
        pdf = generar_pdf_desde_html(correspondencia.contenido_html)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="documento_{pk}.pdf"'
        return response


class AccionCorrespondenciaViewSet(viewsets.ModelViewSet):
    queryset = AccionCorrespondencia.objects.all()
    serializer_class = AccionCorrespondenciaSerializer

    def create(self, request, *args, **kwargs):
        acciones, errores = crear_objetos_multiple(
            self.get_serializer_class(),
            request,
            usuario=request.user,
            extra_fields={'accion': 'DERIVADO'}
        )
        if acciones:
            return Response({'acciones': acciones, 'errores': errores}, status=status.HTTP_201_CREATED)
        return Response({'errores': errores}, status=status.HTTP_400_BAD_REQUEST)


# ===========================
# Notificaciones
# ===========================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notificaciones_pendientes(request):
    acciones = AccionCorrespondencia.objects.filter(
        usuario_destino=request.user, visto=False
    ).select_related('correspondencia').order_by('-fecha')
    
    data = [
        {
            "id_accion": a.id_accion,
            "correspondencia_id": a.correspondencia.id_correspondencia if a.correspondencia else None,
            "documento": a.correspondencia.referencia if a.correspondencia else None,
            "descripcion": a.correspondencia.descripcion if a.correspondencia else "",
            "accion": a.accion,
            "fecha": a.fecha.isoformat(),
            "tipo": a.correspondencia.tipo if a.correspondencia else None,
        } for a in acciones
    ]
    return Response({"count": len(data), "items": data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_notificacion_vista(request, id_accion):
    accion = AccionCorrespondencia.objects.get(id_accion=id_accion, usuario_destino=request.user)
    accion.visto = True
    accion.save(update_fields=['visto'])
    return Response({"status": "ok"})


class HistorialVisualizacionViewSet(viewsets.ModelViewSet):
    queryset = HistorialVisualizacion.objects.all()
    serializer_class = HistorialVisualizacion