from django.db.models import Q
from rest_framework import viewsets

from apps.usuarios.drf_permissions import IsGerenteOuAtendente, IsUsuarioAtivo
from apps.usuarios.models import PerfilUsuario

from .models import Equipamento
from .serializers import EquipamentoSerializer


class EquipamentoPermissionMixin:
    def get_permissions(self):
        permission_class = (
            IsUsuarioAtivo
            if self.request.method in {"GET", "HEAD", "OPTIONS"}
            else IsGerenteOuAtendente
        )
        return [permission_class()]

    def get_queryset(self):
        queryset = Equipamento.objects.select_related("cliente").order_by("-criado_em")
        user = self.request.user
        if user.perfil == PerfilUsuario.TECNICO:
            queryset = queryset.filter(ordens__tecnico=user).distinct()
        cliente = self.request.query_params.get("cliente")
        busca = self.request.query_params.get("q")
        if cliente:
            queryset = queryset.filter(cliente_id=cliente)
        if busca:
            queryset = queryset.filter(
                Q(categoria__icontains=busca)
                | Q(marca__icontains=busca)
                | Q(modelo__icontains=busca)
                | Q(numero_serie__icontains=busca)
            )
        return queryset


class EquipamentoViewSet(EquipamentoPermissionMixin, viewsets.ModelViewSet):
    queryset = Equipamento.objects.all()
    serializer_class = EquipamentoSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]
