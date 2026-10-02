from collections import Counter
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Count
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.financeiro.models import Pagamento
from apps.ordens.models import OrdemServico, SituacaoOrdem
from apps.orcamentos.models import Orcamento, SituacaoOrcamento
from apps.usuarios.drf_permissions import IsGerente

from .serializers import RelatorioFinanceiroSerializer, RelatorioOperacionalSerializer


class RelatorioViewSet(viewsets.ModelViewSet):
    permission_classes = [IsGerente]
    http_method_names = ["get", "head", "options"]

    @action(detail=False, methods=["get"])
    def operacional(self, request, *args, **kwargs):
        ordens = OrdemServico.objects.all()
        situacoes = Counter(ordens.values_list("situacao", flat=True))
        ordens_por_situacao = {
            codigo: situacoes.get(codigo, 0)
            for codigo, _ in SituacaoOrdem.choices
        }

        hoje = timezone.localdate()
        ordens_atrasadas = ordens.filter(
            previsao_entrega__lt=hoje,
        ).exclude(
            situacao__in=[SituacaoOrdem.ENTREGUE, SituacaoOrdem.CANCELADA],
        ).count()

        duracoes = []
        for ordem in ordens.filter(conclusao_em__isnull=False).only(
            "entrada_em",
            "conclusao_em",
        ):
            duracoes.append(
                Decimal(
                    (ordem.conclusao_em - ordem.entrada_em).total_seconds()
                )
                / Decimal("86400")
            )
        tempo_medio = (
            sum(duracoes, Decimal("0.00")) / Decimal(len(duracoes))
            if duracoes
            else Decimal("0.00")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        servicos_por_tecnico = list(
            ordens.filter(
                conclusao_em__isnull=False,
                tecnico__isnull=False,
            )
            .values("tecnico_id", "tecnico__nome")
            .annotate(servicos_concluidos=Count("id"))
            .order_by("tecnico__nome")
        )
        servicos_por_tecnico = [
            {
                "tecnico_id": item["tecnico_id"],
                "tecnico_nome": item["tecnico__nome"],
                "servicos_concluidos": item["servicos_concluidos"],
            }
            for item in servicos_por_tecnico
        ]

        payload = {
            "ordens_por_situacao": ordens_por_situacao,
            "ordens_atrasadas": ordens_atrasadas,
            "tempo_medio_atendimento_dias": tempo_medio,
            "servicos_por_tecnico": servicos_por_tecnico,
            "equipamentos_aguardando_retirada": ordens.filter(
                situacao=SituacaoOrdem.PRONTA_ENTREGA,
            ).count(),
            "retornos": ordens.filter(ordem_original__isnull=False).count(),
        }
        serializer = RelatorioOperacionalSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def financeiro(self, request, *args, **kwargs):
        orcamentos = Orcamento.objects.prefetch_related("itens")
        aprovados = list(orcamentos.filter(situacao=SituacaoOrcamento.APROVADO))
        recusados = orcamentos.filter(situacao=SituacaoOrcamento.RECUSADO).count()
        valor_aprovado = sum(
            (orcamento.total for orcamento in aprovados),
            Decimal("0.00"),
        )

        ordens = OrdemServico.objects.all()
        valor_recebido = sum(
            (
                Pagamento.total_confirmado_para_ordem(ordem.pk)
                for ordem in ordens.only("pk")
            ),
            Decimal("0.00"),
        )
        saldo_pendente = sum(
            (ordem.saldo_pendente for ordem in ordens),
            Decimal("0.00"),
        )
        payload = {
            "orcamentos_aprovados": len(aprovados),
            "orcamentos_recusados": recusados,
            "valor_aprovado": valor_aprovado,
            "valor_recebido": valor_recebido,
            "saldo_pendente": saldo_pendente,
        }
        serializer = RelatorioFinanceiroSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
