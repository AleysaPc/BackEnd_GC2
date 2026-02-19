from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from celery.result import AsyncResult
from django.http import HttpResponse, FileResponse
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend

from .models import Correspondencia, Recibida, Enviada, CorrespondenciaElaborada, AccionCorrespondencia, PreSelloRecibida
from .serializers import (
    CorrespondenciaSerializer, RecibidaSerializer, RecibidaListSerializer,
    EnviadaSerializer, EnviadaListSerializer,
    CorrespondenciaElaboradaSerializer, CorrespondenciaElaboradaListSerializer,
    AccionCorrespondenciaSerializer, PreSelloSerializer
)
from .filters import CorrespondenciaFilter, RecibidaFilter, EnviadaFilter, CorrespondenciaElaboradaFilter
from gestion_documental.mixins import PaginacionYAllDataMixin
from .utils import generar_documento_word, generar_pdf_desde_html
from .services.services import consulta_semantica, crear_objetos_multiple
from django.utils import timezone
from django.utils.timezone import now
from django.template.loader import render_to_string
# Importa tu modelo de usuario personalizado
from usuario.models import CustomUser
from .signals import enviar_correo, construir_mensaje
from .tasks import procesar_ia_pesada_task


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

class PreSelloRecibidaView(BaseViewSet, AuditableModelViewSet):
    serializer_class = PreSelloSerializer
    queryset = PreSelloRecibida.objects.all()

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

    def get_serializer_class(self):
        if self.action == 'list':
            return RecibidaListSerializer
        return RecibidaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related(
            'contacto__institucion',
            'usuario__departamento',
        ).prefetch_related(
            'documentos',
            'acciones__usuario_origen__departamento',
            'acciones__usuario_destino__departamento',
        )
        return queryset

    def create(self, request, *args, **kwargs):
        # 1ï¸âƒ£ Guardar la correspondencia usando el serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        correspondencia = serializer.save()

        # 2ï¸âƒ£ Guardar los usuarios seleccionados (IDs)
        usuarios_ids = request.data.get("usuarios", [])
        if usuarios_ids:
            # Convertir a enteros por si vienen como strings
            usuarios_ids = [int(u) for u in usuarios_ids]
            correspondencia.save()

        # 3ï¸âƒ£ Retornar la respuesta normal del serializer
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["get"], url_path="relaciones")
    def relaciones(self, request, pk=None):
        recibida = self.get_object()

        def _build_hijos(parent_doc):
            hijos = CorrespondenciaElaborada.objects.filter(
                respuesta_a=parent_doc,
            ).order_by("fecha_registro")
            return [
                {
                    "id_correspondencia": h.id_correspondencia,
                    "tipo": h.tipo,
                    "referencia": h.referencia,
                    "numero": getattr(h, "cite", None),
                    "fecha_registro": h.fecha_registro,
                    "hijos": _build_hijos(h),
                }
                for h in hijos
            ]

        relacionada = recibida.relacionada_a
        data = {
            "actual": {
                "id_correspondencia": recibida.id_correspondencia,
                "tipo": recibida.tipo,
                "referencia": recibida.referencia,
                "numero": getattr(recibida, "nro_registro", None),
                "fecha_registro": recibida.fecha_registro,
            },
            "relacionada_a": (
                {
                    "id_correspondencia": relacionada.id_correspondencia,
                    "tipo": relacionada.tipo,
                    "referencia": relacionada.referencia,
                    "numero": getattr(relacionada, "nro_registro", None)
                    or getattr(relacionada, "cite", None),
                    "fecha_registro": relacionada.fecha_registro,
                }
                if relacionada
                else None
            ),
            "respuestas": _build_hijos(recibida),
        }

        return Response(data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def proximo_nro_registro(request):
    """
    Devuelve el prÃ³ximo nro_registro disponible segÃºn la lÃ³gica de la clase Recibida.
    No crea ningÃºn registro en la base de datos.
    """
    # Tomamos la última correspondencia recibida
    ultimo = Recibida.objects.order_by('-id_correspondencia').first()

    if ultimo and ultimo.nro_registro:
        try:
            # Tomamos el número despúes del guion: Reg-001 001
            numero_actual = int(ultimo.nro_registro.split('-')[1])
        except (IndexError, ValueError):
            numero_actual = 0
    else:
        numero_actual = 0

    nuevo_numero = numero_actual + 1
    nro_registro_temporal = f"Reg-{nuevo_numero:03}"

    return Response({"proximo_nro_registro": nro_registro_temporal})

from django.db import transaction
from .models import PreSelloRecibida
from .serializers import PreSelloSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generar_pre_sello(request):
    """
    Genera un pre-sello unico para mostrar en PDF.
    Cada click genera un nuevo unico correlativo, sin crear el registro oficial.
    """
    try:
        with transaction.atomic():
            # Obtener el ultimo número oficial
            ultimo_oficial = Recibida.objects.order_by('-id_correspondencia').first()
            if ultimo_oficial and ultimo_oficial.nro_registro:
                try:
                    numero_actual = int(ultimo_oficial.nro_registro.split('-')[1])
                except (IndexError, ValueError):
                    numero_actual = 0
            else:
                numero_actual = 0

            # Obtener el último pre-sello temporal
            ultimo_pre = PreSelloRecibida.objects.order_by('-id').first()
            if ultimo_pre:
                try:
                    numero_actual = max(numero_actual, int(ultimo_pre.pre_nro_registro.split('-')[1]))
                except (IndexError, ValueError):
                    pass

            nuevo_numero = numero_actual + 1
            pre_nro = f"Reg-{nuevo_numero:03}"

            pre_sello = PreSelloRecibida.objects.create(
                pre_nro_registro=pre_nro,
                usuario=request.user
            )

        serializer = PreSelloSerializer(pre_sello)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response(
            {"error": f"No se pudo generar el pre-sello: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class EnviadaView(BaseViewSet, AuditableModelViewSet):
    serializer_class = EnviadaSerializer
    queryset = Enviada.objects.all().order_by('-fecha_registro')
    filterset_class = EnviadaFilter
    search_fields = ['cite']
    ordering_fields = ['cite']

    def get_serializer_class(self):
        if self.action == 'list':
            return EnviadaListSerializer
        return EnviadaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related(
            'contacto__institucion',
            'usuario__departamento',
        ).prefetch_related(
            'documentos',
            'acciones__usuario_origen__departamento',
            'acciones__usuario_destino__departamento',
        )
        return queryset

    def create(self, request, *args, **kwargs):
        print(" DATA RECIBIDA:", request.data)
        print(" ARCHIVOS:", request.FILES)
        return super().create(request, *args, **kwargs)


# =============================================
# Correspondencia Elaborada (Respuestas)
# =============================================
class CorrespondenciaElaboradaView(BaseViewSet, AuditableModelViewSet):
    queryset = CorrespondenciaElaborada.objects.all().order_by('-fecha_registro')
    serializer_class = CorrespondenciaElaboradaSerializer
    filterset_class = CorrespondenciaElaboradaFilter
    semantic_search_field = 'vector_embedding_html'
    search_fields = [
        'cite', 'referencia','contacto__nombre_contacto','contacto__apellido_pat_contacto',
        'contacto__apellido_mat_contacto','contacto__institucion__razon_social',
        'plantilla__nombre_plantilla','email'
    ]
    ordering_fields = search_fields

    def get_serializer_class(self):
        if self.action == 'list':
            return CorrespondenciaElaboradaListSerializer
        return CorrespondenciaElaboradaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related(
            'contacto__institucion',
            'usuario__departamento',
            'plantilla',
            'destino_interno__departamento',
        ).prefetch_related(
            'documentos',
            'acciones__usuario_origen__departamento',
            'acciones__usuario_destino__departamento',
        )

        if self.action == 'list':
            queryset = queryset.defer(
                'contenido_html',
                'vector_embedding_html',
                'descripcion_introduccion',
                'descripcion_desarrollo',
                'descripcion_conclusion',
            )

        return queryset

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
        destino_id = request.data.get("usuario_destino", None)
        correspondencia_origen = None
        usuario_destino = None

        if respuesta_a:
            try:
                # El origen puede ser recibida o elaborada.
                correspondencia_origen = Correspondencia.objects.get(
                    id_correspondencia=respuesta_a
                )
            except Correspondencia.DoesNotExist:
                return Response(
                    {"error": "El documento origen no existe."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            usuario_destino = correspondencia_origen.usuario
            if destino_id:
                try:
                    usuario_destino = User.objects.get(pk=destino_id)
                except User.DoesNotExist:
                    return Response(
                        {"error": "El usuario destino no existe."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            if usuario_destino and request.user == usuario_destino:
                return Response(
                    {"error": "No puedes derivarte a ti mismo."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        elaborada = serializer.save()

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
        return Response({"error": "NotificaciÃ³n no encontrada"}, status=status.HTTP_404_NOT_FOUND)

    if not accion.visto:
        accion.visto = True
        accion.fecha_visto = timezone.now()
        accion.save(update_fields=['visto', 'fecha_visto'])
        return Response({"status": "ok"})

    return Response({"error": "NotificaciÃ³n ya vista"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def iniciar_tarea_ia(request):
    texto = request.data.get("texto", "")
    if not texto:
        return Response({"error": "Debe enviar el campo 'texto'."}, status=status.HTTP_400_BAD_REQUEST)

    task = procesar_ia_pesada_task.delay(texto)
    return Response({"task_id": task.id, "status": "PENDING"}, status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def estado_tarea_ia(request, task_id):
    task = AsyncResult(task_id)
    payload = {"task_id": task.id, "status": task.status}

    if task.successful():
        payload["result"] = task.result
    elif task.failed():
        payload["error"] = str(task.result)

    return Response(payload, status=status.HTTP_200_OK)

