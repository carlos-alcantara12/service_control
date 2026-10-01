from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.usuarios.drf_permissions import IsUsuarioAtivo
from apps.usuarios.models import PerfilUsuario

from .models import Orcamento
from .serializers import (
    DecisaoOrcamentoCreateSerializer,
    DecisaoOrcamentoSerializer,
    OrcamentoEnviarSerializer,
    OrcamentoSerializer,
)


class OrcamentoQuerysetMixin:
    def get_queryset(self):
        queryset = (
            Orcamento.objects.select_related(
                "ordem",
                "ordem__cliente",
                "ordem__equipamento",
                "criador",
            )
            .prefetch_related("itens", "decisao")
            .order_by("-criado_em", "-versao")
        )
        user = self.request.user
        if getattr(user, "perfil", None) == PerfilUsuario.TECNICO:
            queryset = queryset.filter(ordem__tecnico=user)

        situacao = self.request.query_params.get("situacao")
        if situacao:
            queryset = queryset.filter(situacao=situacao)
        ordem = self.request.query_params.get("ordem")
        if ordem:
            queryset = queryset.filter(ordem_id=ordem)
        busca = self.request.query_params.get("q")
        if busca:
            queryset = queryset.filter(
                Q(ordem__numero__icontains=busca)
                | Q(ordem__cliente__nome__icontains=busca)
                | Q(observacoes__icontains=busca)
            )
        return queryset


class OrcamentoViewSet(
    OrcamentoQuerysetMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Orcamento.objects.all()
    permission_classes = [IsUsuarioAtivo]
    serializer_class = OrcamentoSerializer
    http_method_names = ["get", "post", "head", "options"]

    @action(detail=True, methods=["post"])
    def enviar(self, request, *args, **kwargs):
        orcamento = self.get_object()
        context = self.get_serializer_context()
        context["orcamento"] = orcamento
        serializer = OrcamentoEnviarSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        resultado = serializer.save()
        return Response(
            OrcamentoSerializer(
                resultado,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def decisao(self, request, *args, **kwargs):
        orcamento = self.get_object()
        context = self.get_serializer_context()
        context["orcamento"] = orcamento
        serializer = DecisaoOrcamentoCreateSerializer(
            data=request.data,
            context=context,
        )
        serializer.is_valid(raise_exception=True)
        resultado = serializer.save()
        return Response(
            DecisaoOrcamentoSerializer(
                resultado,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_200_OK,
        )
