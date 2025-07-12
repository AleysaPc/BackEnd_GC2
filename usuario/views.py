from rest_framework import viewsets, permissions, status
from .serializers import * 
from .models import * 
from rest_framework.response import Response 
from django.contrib.auth import get_user_model, authenticate
from knox.models import AuthToken
from gestion_documental.mixins import PaginacionYAllDataMixin

User = get_user_model()

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
                return Response(
                    {
                        "user": self.serializer_class(user).data,
                        "token": token
                    }
                )
            else: 
                return Response({"error":"Invalid credentials"}, status=401)    
        else: 
            return Response(serializer.errors,status=400)

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

class DepartamentoViewSet(viewsets.ModelViewSet):
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer
    
class CustomUserViewSet(PaginacionYAllDataMixin ,viewsets.ModelViewSet):
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]
    queryset = CustomUser.objects.all().order_by('id')  # Ordena por id_producto en lugar de id

    def list(self, request, *args, **kwargs):
        all_data = request.query_params.get('all_data', 'false').lower() == 'true'  # Convierte a booleano correctamente

        if all_data:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return super().list(request, *args, **kwargs)  # Usa la paginación normal

