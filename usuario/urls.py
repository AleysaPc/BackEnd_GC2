from django.urls import path, include
from rest_framework.routers import DefaultRouter
from knox import views as knox_views
from .views import *

router = DefaultRouter()
router.register('customuser', UsuarioViewSet, basename='customuser')
router.register('departamentos', DepartamentoViewSet, basename="departamento")
router.register('permisos', PermisoViewSet, basename="permiso")
router.register('roles', RolViewSet, basename="rol")

login_view = LoginViewset.as_view({'post': 'create'})

urlpatterns = [
    path('', include(router.urls)),  # Usa el router para recursos CRUD
    path('login/', login_view, name='login'),
    path('logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    path('logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),

    # Listados
    path('usuarios-list/', UsuarioListViewSet.as_view(), name='usuario-list'),
    path('departamento-list/', DepartamentoListViewSet.as_view(), name='departamento-list'),
    path('roles-list/', RolListViewSet.as_view(), name='rol-list'),
    path('departamento-select/', DepartamentoSelectViewSet.as_view(), name='departamento-select'),
    path('permisos-list/', PermisoListViewSet.as_view(), name='permiso-list'), #Se obtiene toda la lista de permisos
]