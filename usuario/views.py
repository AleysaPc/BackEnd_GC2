from rest_framework import mixins, viewsets, permissions, generics
from .serializers import * 
from .models import * 
from rest_framework.response import Response 
from django.contrib.auth import get_user_model, authenticate
from knox.models import AuthToken
from gestion_documental.mixins import PaginacionYAllDataMixin
from django.contrib.auth.models import Group, Permission
from .filters import CustomUserFilter
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

User = get_user_model()

# -------------------------------
# Login
# -------------------------------
class LoginViewset(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(request, email=email, password=password)
            if user:
                _, token = AuthToken.objects.create(user)
                return Response({
                    "user": self.serializer_class(user).data,
                    "token": token
                })
            else:
                return Response({"error": "Invalid credentials"}, status=401)
        else:
            return Response(serializer.errors, status=400)
    
# -------------------------------
# CRUD SIN LISTADO
# -------------------------------
class UsuarioViewSet(
    mixins.RetrieveModelMixin,   # GET por id
    mixins.CreateModelMixin,     # POST
    mixins.UpdateModelMixin,     # PUT / PATCH
    mixins.DestroyModelMixin,    # DELETE
    viewsets.GenericViewSet
):
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = CustomUser.objects.all()

class PermisoViewSet(
    mixins.RetrieveModelMixin,   # GET por id
    mixins.CreateModelMixin,     # POST
    mixins.UpdateModelMixin,     # PUT / PATCH
    mixins.DestroyModelMixin,    # DELETE
    viewsets.GenericViewSet
):
    serializer_class = PermisoSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Permission.objects.all()

class RolViewSet(
    mixins.RetrieveModelMixin,   # GET por id
    mixins.CreateModelMixin,     # POST
    mixins.UpdateModelMixin,     # PUT / PATCH
    mixins.DestroyModelMixin,    # DELETE
    viewsets.GenericViewSet
):
    serializer_class = RolSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Group.objects.all()

class DepartamentoViewSet(
    mixins.RetrieveModelMixin,   # GET por id
    mixins.CreateModelMixin,     # POST
    mixins.UpdateModelMixin,     # PUT / PATCH
    mixins.DestroyModelMixin,    # DELETE
    viewsets.GenericViewSet
):
    serializer_class = DepartamentoSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Departamento.objects.all()

# -------------------------------
# LISTADOS
# -------------------------------
class UsuarioListViewSet(PaginacionYAllDataMixin, generics.ListAPIView):
    serializer_class = UsuarioListSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = CustomUser.objects.all().order_by('-date_joined')
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = CustomUserFilter
    search_fields = [
        'first_name', 'last_name', 'second_name', 'second_last_name', 'username', 'email', 'institucion__razon_social'
    ]
    ordering_fields = ['first_name', 'last_name', 'second_name', 'second_last_name', 'username', 'email', 'institucion__razon_social']
    
class PermisoListViewSet(PaginacionYAllDataMixin, generics.ListAPIView):
    serializer_class = PermisoSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = Permission.objects.all().order_by('-id')

class RolListViewSet(PaginacionYAllDataMixin, generics.ListAPIView):
    serializer_class = RolListSerializer
    # permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Group.objects.only("id", "name").order_by("name")

class RolSelectDualViewSet(PaginacionYAllDataMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = RolSelectDualSerializer
    # permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Group.objects.only("id", "name").order_by("name")

class DepartamentoListViewSet(PaginacionYAllDataMixin, generics.ListAPIView):
    serializer_class = DepartamentoListSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = Departamento.objects.all().order_by('-id')

class PermisoListViewSet(PaginacionYAllDataMixin, generics.ListAPIView):
    serializer_class = PermisosListSerializer
    # permission_classes = [permissions.IsAuthenticated]
    queryset = Permission.objects.only("id", "name").order_by("name")

# -------------------------------
# SELECTS
# -------------------------------
class DepartamentoSelectViewSet(PaginacionYAllDataMixin, generics.ListAPIView):
    serializer_class = DepartamentoSelectSerializer
    def get_queryset(self):
        return Departamento.objects.only("id", "nombre").order_by('nombre')