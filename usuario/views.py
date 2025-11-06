from rest_framework import viewsets, permissions, status
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

class GroupViewSet(PaginacionYAllDataMixin, viewsets.ModelViewSet):
    """
    CRUD completo para Grupos y asignación de permisos
    """
    queryset = Group.objects.all().order_by('id')
    serializer_class = GroupSerializer
    # permission_classes = [permissions.IsAuthenticated] # Así cualquiera puede ver

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Listar y detallar permisos disponibles
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    # permission_classes = [permissions.IsAuthenticated]

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


class DepartamentoViewSet(viewsets.ModelViewSet):
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer
    
class CustomUserViewSet(PaginacionYAllDataMixin ,viewsets.ModelViewSet):
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]
    queryset = CustomUser.objects.all().order_by('-date_joined')  # Ordena por id_producto en lugar de id

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
    
