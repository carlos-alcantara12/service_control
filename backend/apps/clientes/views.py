from django.db.models import Q
from rest_framework import viewsets

from apps.usuarios.drf_permissions import IsGerenteOuAtendente, IsUsuarioAtivo
from apps.usuarios.models import PerfilUsuario

from .models import Cliente
from .serializers import ClienteSerializer


class ClientePermissionMixin:
    def get_permissions(self):
        permission_class = (
            IsUsuarioAtivo
            if self.request.method in {"GET", "HEAD", "OPTIONS"}
            else IsGerenteOuAtendente
        )
        return [permission_class()]

    def get_queryset(self):
        queryset = Cliente.objects.all().order_by("nome")
        user = self.request.user
        if user.perfil == PerfilUsuario.TECNICO:
            queryset = queryset.filter(
                equipamentos__ordens__tecnico=user,
            ).distinct()
        ativo = self.request.query_params.get("ativo")
        busca = self.request.query_params.get("q")
        if ativo in {"0", "1", "true", "false"}:
            queryset = queryset.filter(ativo=ativo in {"1", "true"})
        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca)
                | Q(telefone__icontains=busca)
                | Q(documento__icontains=busca)
            )
        return queryset


class ClienteViewSet(ClientePermissionMixin, viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]
