from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone


class FormaPagamento(models.TextChoices):
    DINHEIRO = "DINHEIRO", "Dinheiro"
    PIX = "PIX", "PIX"
    CARTAO_CREDITO = "CARTAO_CREDITO", "Cartão de crédito"
    CARTAO_DEBITO = "CARTAO_DEBITO", "Cartão de débito"
    TRANSFERENCIA = "TRANSFERENCIA", "Transferência"
    OUTRO = "OUTRO", "Outro"


class SituacaoPagamento(models.TextChoices):
    PENDENTE = "PENDENTE", "Pendente"
    CONFIRMADO = "CONFIRMADO", "Confirmado"
    ESTORNADO = "ESTORNADO", "Estornado"
    CANCELADO = "CANCELADO", "Cancelado"


class Pagamento(models.Model):
    ordem = models.ForeignKey(
        "ordens.OrdemServico",
        on_delete=models.PROTECT,
        related_name="pagamentos",
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pagamentos_registrados",
    )
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    forma = models.CharField(max_length=20, choices=FormaPagamento.choices)
    situacao = models.CharField(
        max_length=15,
        choices=SituacaoPagamento.choices,
        default=SituacaoPagamento.CONFIRMADO,
    )
    pago_em = models.DateTimeField(default=timezone.now)
    referencia = models.CharField(max_length=255, blank=True)
    identificador_operacao = models.CharField(max_length=100, unique=True)

    @classmethod
    def total_confirmado_para_ordem(cls, ordem_id):
        total = cls.objects.filter(
            ordem_id=ordem_id,
            situacao=SituacaoPagamento.CONFIRMADO,
        ).aggregate(total=Sum("valor"))["total"]
        estornos = Estorno.objects.filter(
            pagamento__ordem_id=ordem_id,
        ).aggregate(total=Sum("valor"))["total"]
        return (total or Decimal("0.00")) - (estornos or Decimal("0.00"))

    class Meta:
        ordering = ["-pago_em"]
        indexes = [
            models.Index(fields=["situacao", "pago_em"]),
            models.Index(fields=["ordem", "pago_em"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(valor__gt=0),
                name="pagamento_valor_maior_que_zero",
            ),
        ]
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"


class Estorno(models.Model):
    pagamento = models.ForeignKey(
        Pagamento,
        on_delete=models.PROTECT,
        related_name="estornos",
    )
    autorizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="estornos_autorizados",
    )
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    motivo = models.TextField()
    registrado_em = models.DateTimeField(default=timezone.now, editable=False)

    def clean(self):
        super().clean()
        if not self.pagamento_id:
            return
        estornos_anteriores = self.pagamento.estornos.exclude(pk=self.pk).aggregate(
            total=Sum("valor")
        )["total"] or Decimal("0.00")
        if estornos_anteriores + self.valor > self.pagamento.valor:
            raise ValidationError({"valor": "A soma dos estornos não pode superar o pagamento."})

    class Meta:
        ordering = ["-registrado_em"]
        constraints = [
            models.CheckConstraint(
                condition=Q(valor__gt=0),
                name="estorno_valor_maior_que_zero",
            ),
        ]
        verbose_name = "Estorno"
        verbose_name_plural = "Estornos"


class TratamentoFinanceiroCancelamento(models.TextChoices):
    SEM_COBRANCA = "SEM_COBRANCA", "Sem cobrança"
    DEVOLVER_PAGAMENTO = "DEVOLVER_PAGAMENTO", "Devolver pagamento"
    MANTER_CREDITO = "MANTER_CREDITO", "Manter como crédito"
    OUTRO = "OUTRO", "Outro"


class Cancelamento(models.Model):
    ordem = models.OneToOneField(
        "ordens.OrdemServico",
        on_delete=models.PROTECT,
        related_name="cancelamento",
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cancelamentos_registrados",
    )
    motivo = models.TextField()
    tratamento_financeiro = models.CharField(
        max_length=25,
        choices=TratamentoFinanceiroCancelamento.choices,
    )
    registrado_em = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        verbose_name = "Cancelamento"
        verbose_name_plural = "Cancelamentos"
