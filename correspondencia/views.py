from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse, FileResponse
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend

from .models import Correspondencia, Recibida, Enviada, CorrespondenciaElaborada, AccionCorrespondencia
from .serializers import (
    CorrespondenciaSerializer, RecibidaSerializer, EnviadaSerializer, 
    CorrespondenciaElaboradaSerializer, AccionCorrespondenciaSerializer
)
from .filters import CorrespondenciaFilter, RecibidaFilter, EnviadaFilter, CorrespondenciaElaboradaFilter
from gestion_documental.mixins import PaginacionYAllDataMixin
from .utils import generar_documento_word, generar_pdf_desde_html
from .services.services import consulta_semantica, crear_objetos_multiple
from django.utils import timezone
from django.utils.timezone import now
from django.template.loader import render_to_string


User = get_user_model()

# =============================================
# ViewSet base para auditoría
# =============================================
class AuditableModelViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        if hasattr(serializer.Meta.model, 'usuario_origen'):
            serializer.save(usuario_origen=self.request.user)
        elif hasattr(serializer.Meta.model, 'usuario'):
            serializer.save(usuario=self.request.user)
        else:
            serializer.save()

    def perform_update(self, serializer):
        data = {}
        if hasattr(serializer.Meta.model, 'ultima_modificacion'):
            data['ultima_modificacion'] = self.request.user
        if hasattr(serializer.Meta.model, 'fecha_modificacion'):
            data['fecha_modificacion'] = timezone.now()
        serializer.save(**data)


# =============================================
# Clase base general para ViewSets
# =============================================
class BaseViewSet(PaginacionYAllDataMixin, viewsets.ModelViewSet):
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


# =============================================
# Documentos Word
# =============================================
def generar_documento(request, doc_id):
    correspondencia = get_object_or_404(CorrespondenciaElaborada, pk=doc_id)
    buffer, filename = generar_documento_word(correspondencia)
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=filename,
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


# =============================================
# VIEWSETS
# =============================================
class CorrespondenciaView(BaseViewSet, AuditableModelViewSet):
    serializer_class = CorrespondenciaSerializer
    queryset = Correspondencia.objects.all()
    filterset_class = CorrespondenciaFilter
    search_fields = ['tipo', 'referencia', 'contacto__institucion__razon_social']
    ordering_fields = ['tipo', 'referencia']


class RecibidaView(BaseViewSet, AuditableModelViewSet):
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
        print("📥 DATA RECIBIDA:", request.data)
        print("📎 ARCHIVOS:", request.FILES)
        return super().create(request, *args, **kwargs)


class EnviadaView(BaseViewSet, AuditableModelViewSet):
    serializer_class = EnviadaSerializer
    queryset = Enviada.objects.all().order_by('-fecha_registro')
    filterset_class = EnviadaFilter
    search_fields = ['cite']
    ordering_fields = ['cite']

    def create(self, request, *args, **kwargs):
        print("📤 DATA RECIBIDA:", request.data)
        print("📎 ARCHIVOS:", request.FILES)
        return super().create(request, *args, **kwargs)


# =============================================
# Correspondencia Elaborada (Respuestas)
# =============================================
class CorrespondenciaElaboradaView(BaseViewSet, AuditableModelViewSet):
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
        
        html_completo = render_to_string("Documento/base_documento.html", {
            "contenido": correspondencia.contenido_html,
            "url_membrete_superior": request.build_absolute_uri("/media/Membrete.PNG"),
            "url_sello": request.build_absolute_uri("/media/Sello.PNG"),
            "url_membrete_inferior": request.build_absolute_uri("/media/MembreteInferior.PNG"),
        })
        
        pdf = generar_pdf_desde_html(html_completo)
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="documento_{pk}.pdf"'
        return response


    def create(self, request, *args, **kwargs):
        respuesta_a = request.data.get("respuesta_a", None)
        destino_id = request.data.get("usuario_destino", None)  # 🔹 NUEVO: usuario al que derivar

        # Serializar y guardar la correspondencia
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        elaborada = serializer.save()

        if respuesta_a:
            try:
                # Obtener la correspondencia recibida
                recibida = Recibida.objects.get(id_correspondencia=respuesta_a)

                # Cambiar estado SOLO aquí
                recibida.estado_actual = "Respondido"
                recibida.save(update_fields=["estado_actual"])

                elaborada.respuesta_a_id = respuesta_a
                elaborada.save(update_fields=["respuesta_a_id"])

                # 🔹 NUEVO: determinar usuario_destino real
                # Determinar usuario_destino real
                # Determinar usuario_destino
                usuario_destino = recibida.usuario  # valor por defecto
                if destino_id:
                    try:
                        usuario_destino = User.objects.get(pk=destino_id)
                    except User.DoesNotExist:
                        pass  # se mantiene el valor por defecto

                # Evitar derivarse a sí mismo
                if request.user == usuario_destino:
                    return Response(
                        {"error": "No puedes derivarte a ti mismo."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Crear acción
                AccionCorrespondencia.objects.create(
                    correspondencia=recibida,
                    usuario_origen=request.user,
                    usuario_destino=usuario_destino,
                    accion="respondido",
                    comentario=f"Respuesta generada: {elaborada.cite}",
                    estado_resultante="respondido"
                )



            except Recibida.DoesNotExist:
                pass

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# =============================================
# Acciones (NO cambian estado por defecto)
# =============================================
class AccionCorrespondenciaViewSet(viewsets.ModelViewSet):
    queryset = AccionCorrespondencia.objects.all()
    serializer_class = AccionCorrespondenciaSerializer

    def perform_create(self, serializer):
        accion_creada = serializer.save()
        correspondencia = accion_creada.correspondencia

        # Caso: una Correspondencia Elaborada que ya respondió a una Recibida
        if isinstance(correspondencia, CorrespondenciaElaborada) and correspondencia.respuesta_a:
            recibida_original = correspondencia.respuesta_a

            # Crear acción espejo
            AccionCorrespondencia.objects.create(
                correspondencia=recibida_original,
                usuario_origen=accion_creada.usuario_origen,
                usuario_destino=accion_creada.usuario_destino,
                accion="respondido",
                comentario=f"Respuesta generada: {correspondencia.cite}",
                estado_resultante="respondido"
            )

            # El estado YA fue cambiado en CorrespondenciaElaboradaView.create()

        return accion_creada


# =============================================
# NOTIFICACIONES
# =============================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notificaciones_pendientes(request):
    acciones = (
        AccionCorrespondencia.objects
        .filter(usuario_destino=request.user, visto=False)
        .select_related('correspondencia')
        .order_by('-fecha_inicio')
    )
    
    data = [
       {
            "id": a.id,
            "correspondencia_id": getattr(a.correspondencia, "id_correspondencia", None),
            "referencia": getattr(a.correspondencia, "referencia", None),
            "comentario": a.comentario,
            "accion": a.accion,
            "fecha": a.fecha_inicio.isoformat() if a.fecha_inicio else None,
            "tipo": getattr(a.correspondencia, "tipo", None),
        }
        for a in acciones
    ]

    return Response({"count": len(data), "items": data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_notificacion_vista(request, id):
    try:
        accion = AccionCorrespondencia.objects.get(id=id, usuario_destino=request.user)
    except AccionCorrespondencia.DoesNotExist:
        return Response({"error": "Notificación no encontrada"}, status=status.HTTP_404_NOT_FOUND)

    if not accion.visto:
        accion.visto = True
        accion.fecha_visto = timezone.now()
        accion.save(update_fields=['visto', 'fecha_visto'])
        return Response({"status": "ok"})

    return Response({"error": "Notificación ya vista"}, status=status.HTTP_400_BAD_REQUEST)
