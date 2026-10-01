from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.auditoria.models import HistoricoAlteracao
from apps.auditoria.serializers import HistoricoAlteracaoSerializer
from apps.financeiro.serializers import (
    CancelamentoCreateSerializer,
    CancelamentoSerializer,
    PagamentoCreateSerializer,
    PagamentoSerializer,
)
from apps.orcamentos.serializers import (
    OrcamentoCreateSerializer,
    OrcamentoSerializer,
)
from apps.usuarios.drf_permissions import IsUsuarioAtivo

from .models import Anexo, OrdemServico, SituacaoOrdem
from .serializers import (
    AnexoSerializer,
    AnexoUploadSerializer,
    AtribuirTecnicoSerializer,
    AtividadeCreateSerializer,
    AtividadeServicoSerializer,
    AlterarPrazoSerializer,
    ConcluirTestesSerializer,
    DiagnosticoSerializer,
    EntregaCreateSerializer,
    EntregaSerializer,
    IniciarReparoSerializer,
    OrdemServicoCreateSerializer,
    OrdemServicoDetalheSerializer,
    OrdemServicoSerializer,
    PecaUtilizadaCreateSerializer,
    PecaUtilizadaSerializer,
    RetornoCreateSerializer,
)


class OrdemQuerysetMixin:
    def get_queryset(self):
        queryset = OrdemServico.objects.select_related(
            "cliente",
            "equipamento",
            "atendente",
            "tecnico",
            "ordem_original",
        ).order_by("-entrada_em")
        user = self.request.user
        if getattr(user, "perfil", None) == "TECNICO":
            queryset = queryset.filter(tecnico=user)

        for field in ("situacao", "prioridade", "cliente", "equipamento", "tecnico"):
            value = self.request.query_params.get(field)
            if value:
                filter_field = (
                    f"{field}_id"
                    if field in {"cliente", "equipamento", "tecnico"}
                    else field
                )
                queryset = queryset.filter(**{filter_field: value})

        busca = self.request.query_params.get("q")
        if busca:
            queryset = queryset.filter(
                Q(numero__icontains=busca)
                | Q(defeito_relatado__icontains=busca)
                | Q(diagnostico__icontains=busca)
            )

        if self.request.query_params.get("atrasadas") in {"1", "true"}:
            queryset = queryset.filter(
                previsao_entrega__lt=timezone.localdate(),
            ).exclude(
                situacao__in=[SituacaoOrdem.ENTREGUE, SituacaoOrdem.CANCELADA],
            )
        return queryset


class OrdemServicoViewSet(OrdemQuerysetMixin, viewsets.ModelViewSet):
    queryset = OrdemServico.objects.all()
    permission_classes = [IsUsuarioAtivo]
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return OrdemServicoCreateSerializer
        if self.action == "retrieve":
            return OrdemServicoDetalheSerializer
        return OrdemServicoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        ordem = serializer.save()
        return Response(
            OrdemServicoSerializer(
                ordem,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def _execute_order_action(
        self,
        request,
        serializer_class,
        output_serializer_class=OrdemServicoSerializer,
    ):
        ordem = self.get_object()
        context = self.get_serializer_context()
        context["ordem"] = ordem
        serializer = serializer_class(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        resultado = serializer.save()
        return Response(
            output_serializer_class(
                resultado,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="atribuir-tecnico")
    def atribuir_tecnico(self, request, *args, **kwargs):
        return self._execute_order_action(request, AtribuirTecnicoSerializer)

    @action(detail=True, methods=["post"])
    def diagnostico(self, request, *args, **kwargs):
        return self._execute_order_action(request, DiagnosticoSerializer)

    @action(detail=True, methods=["post"], url_path="alterar-prazo")
    def alterar_prazo(self, request, *args, **kwargs):
        return self._execute_order_action(request, AlterarPrazoSerializer)

    @action(detail=True, methods=["post"], url_path="iniciar-reparo")
    def iniciar_reparo(self, request, *args, **kwargs):
        return self._execute_order_action(request, IniciarReparoSerializer)

    @action(detail=True, methods=["post"])
    def atividades(self, request, *args, **kwargs):
        return self._execute_order_action(
            request,
            AtividadeCreateSerializer,
            AtividadeServicoSerializer,
        )

    @action(detail=True, methods=["post"])
    def pecas(self, request, *args, **kwargs):
        return self._execute_order_action(
            request,
            PecaUtilizadaCreateSerializer,
            PecaUtilizadaSerializer,
        )

    @action(detail=True, methods=["post"], url_path="concluir-testes")
    def concluir_testes(self, request, *args, **kwargs):
        return self._execute_order_action(request, ConcluirTestesSerializer)

    @action(detail=True, methods=["post"])
    def entrega(self, request, *args, **kwargs):
        return self._execute_order_action(
            request,
            EntregaCreateSerializer,
            EntregaSerializer,
        )

    @action(detail=True, methods=["post"])
    def retornos(self, request, *args, **kwargs):
        return self._execute_order_action(request, RetornoCreateSerializer)

    @action(detail=True, methods=["post"])
    def orcamentos(self, request, *args, **kwargs):
        ordem = self.get_object()
        context = self.get_serializer_context()
        context["ordem"] = ordem
        serializer = OrcamentoCreateSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        orcamento = serializer.save()
        return Response(
            OrcamentoSerializer(
                orcamento,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def pagamentos(self, request, *args, **kwargs):
        ordem = self.get_object()
        context = self.get_serializer_context()
        context["ordem"] = ordem
        serializer = PagamentoCreateSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        pagamento = serializer.save()
        return Response(
            PagamentoSerializer(
                pagamento,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def cancelamento(self, request, *args, **kwargs):
        ordem = self.get_object()
        context = self.get_serializer_context()
        context["ordem"] = ordem
        serializer = CancelamentoCreateSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        cancelamento = serializer.save()
        return Response(
            CancelamentoSerializer(
                cancelamento,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get", "post"])
    def anexos(self, request, *args, **kwargs):
        ordem = self.get_object()
        if request.method == "GET":
            queryset = ordem.anexos.select_related("enviado_por").all()
            return Response(
                AnexoSerializer(
                    queryset,
                    many=True,
                    context=self.get_serializer_context(),
                ).data
            )

        context = self.get_serializer_context()
        context["ordem"] = ordem
        serializer = AnexoUploadSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        anexo = serializer.save()
        return Response(
            AnexoSerializer(
                anexo,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def historico(self, request, *args, **kwargs):
        ordem = self.get_object()
        queryset = HistoricoAlteracao.objects.select_related("usuario").filter(ordem=ordem)
        return Response(
            HistoricoAlteracaoSerializer(
                queryset,
                many=True,
                context=self.get_serializer_context(),
            ).data
        )
