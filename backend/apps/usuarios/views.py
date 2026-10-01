from django.contrib.auth import authenticate, login, logout
from rest_framework import status, viewsets
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView

from .drf_permissions import IsGerente, IsUsuarioAtivo
from .models import PerfilUsuario, Usuario
from .serializers import LoginSerializer, UsuarioSerializer


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request=request,
            username=serializer.validated_data["login"],
            password=serializer.validated_data["password"],
        )
        if not user or not getattr(user, "ativo", False):
            raise AuthenticationFailed("Login ou senha inválidos.")
        login(request, user)
        return Response(UsuarioSerializer(user, context={"request": request}).data)


class LogoutView(APIView):
    permission_classes = [IsUsuarioAtivo]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsGerente]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = Usuario.objects.all().order_by("nome")
        perfil = self.request.query_params.get("perfil")
        ativo = self.request.query_params.get("ativo")
        busca = self.request.query_params.get("q")
        if perfil in PerfilUsuario.values:
            queryset = queryset.filter(perfil=perfil)
        if ativo in {"0", "1", "true", "false"}:
            queryset = queryset.filter(ativo=ativo in {"1", "true"})
        if busca:
            queryset = queryset.filter(nome__icontains=busca)
        return queryset
