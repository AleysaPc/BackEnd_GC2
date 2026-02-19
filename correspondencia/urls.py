from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CorrespondenciaView,
    PreSelloRecibidaView,
    RecibidaView,
    EnviadaView,
    CorrespondenciaElaboradaView,
    AccionCorrespondenciaViewSet,
    generar_documento,
    generar_pre_sello,
    notificaciones_pendientes,
    marcar_notificacion_vista,
    proximo_nro_registro,
    iniciar_tarea_ia,
    estado_tarea_ia,
)

router = DefaultRouter()
router.register(r"correspondencia", CorrespondenciaView)
router.register(r"recibida", RecibidaView)
router.register(r"enviada", EnviadaView)
router.register(r"elaborada", CorrespondenciaElaboradaView)
router.register(r"acciones", AccionCorrespondenciaViewSet, basename="acciones")
router.register(r"preSello", PreSelloRecibidaView)

urlpatterns = [
    path("", include(router.urls)),
    path("generar_documento/<int:doc_id>/", generar_documento, name="generar_documento"),
    path("notificacion/pendiente/", notificaciones_pendientes, name="notificaciones_pendientes"),
    path("notificacion/vista/<int:id>/", marcar_notificacion_vista, name="marcar_notificacion_vista"),
    path("ia/tarea/iniciar/", iniciar_tarea_ia, name="iniciar_tarea_ia"),
    path("ia/tarea/estado/<str:task_id>/", estado_tarea_ia, name="estado_tarea_ia"),
    path("proximo_nro_registro/", proximo_nro_registro),
    path("generar_pre_sello/", generar_pre_sello),
]
