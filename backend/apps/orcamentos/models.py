from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class SituacaoOrcamento(models.TextChoices):
    RASCUNHO = "RASCUNHO", "Rascunho"
    ENVIADO = "ENVIADO", "Enviado"
    APROVADO = "APROVADO", "Aprovado"
    RECUSADO = "RECUSADO", "Recusado"
    EXPIRADO = "EXPIRADO", "Expirado"
    SUBSTITUIDO = "SUBSTITUIDO", "Substituído"


class Orcamento(models.Model):
    ordem = models.ForeignKey(
        "ordens.OrdemServico",
        on_delete=models.PROTECT,
        related_name="orcamentos",
    )
    criador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orcamentos_criados",
    )
    versao = models.PositiveIntegerField()
    situacao = models.CharField(
        max_length=20,
        choices=SituacaoOrcamento.choices,
        default=SituacaoOrcamento.RASCUNHO,
    )
    criado_em = models.DateTimeField(default=timezone.now, editable=False)
    enviado_em = models.DateTimeField(null=True, blank=True)
    valido_ate = models.DateField(null=True, blank=True)
    observacoes = models.TextField(blank=True)

    @property
    def total(self):
        return self.calcular_total()

    def calcular_total(self):
        return sum(
            (item.quantidade * item.valor_unitario for item in self.itens.all()),
            Decimal("0.00"),
        )

    def save(self, *args, **kwargs):
        if self.situacao == SituacaoOrcamento.ENVIADO:
            if not self.pk:
                raise ValidationError(
                    "Crie o orçamento como rascunho e envie-o depois de adicionar os itens."
                )
            if not self.itens.exists():
                raise ValidationError("Um orçamento precisa ter pelo menos um item para ser enviado.")
        if self.pk:
            original = type(self).objects.only(
                "ordem_id", "criador_id", "versao", "situacao"
            ).get(pk=self.pk)
            if original.situacao != SituacaoOrcamento.RASCUNHO and any(
                (
                    self.ordem_id != original.ordem_id,
                    self.criador_id != original.criador_id,
                    self.versao != original.versao,
                )
            ):
                raise ValidationError("A versão de um orçamento enviado não pode ser reescrita.")
        return super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.versao is not None and self.versao < 1:
            raise ValidationError({"versao": "A versão deve ser positiva."})
        if self.situacao == SituacaoOrcamento.ENVIADO:
            if not self.pk:
                raise ValidationError(
                    "Crie o orçamento como rascunho e envie-o depois de adicionar os itens."
                )
            if not self.itens.exists():
                raise ValidationError("Um orçamento precisa ter pelo menos um item para ser enviado.")
            if not self.valido_ate:
                raise ValidationError({"valido_ate": "Informe a validade do orçamento enviado."})
            if self.valido_ate < timezone.localdate():
                raise ValidationError({"valido_ate": "A validade não pode estar no passado ao enviar."})

    def __str__(self):
        return f"{self.ordem.numero} — v{self.versao}"

    class Meta:
        ordering = ["-versao"]
        constraints = [
            models.UniqueConstraint(
                fields=["ordem", "versao"],
                name="orcamento_ordem_versao_unicas",
            ),
            models.CheckConstraint(
                condition=Q(versao__gte=1),
                name="orcamento_versao_positiva",
            ),
        ]
        indexes = [
            models.Index(fields=["situacao", "valido_ate"]),
            models.Index(fields=["ordem", "versao"]),
        ]
        verbose_name = "Orçamento"
        verbose_name_plural = "Orçamentos"


class TipoItemOrcamento(models.TextChoices):
    SERVICO = "SERVICO", "Serviço"
    PECA = "PECA", "Peça"
    OUTRO = "OUTRO", "Outro"


class ItemOrcamento(models.Model):
    orcamento = models.ForeignKey(
        Orcamento,
        on_delete=models.PROTECT,
        related_name="itens",
    )
    tipo = models.CharField(max_length=10, choices=TipoItemOrcamento.choices)
    descricao = models.CharField(max_length=255)
    quantidade = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    valor_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    @property
    def total(self):
        return self.quantidade * self.valor_unitario

    def save(self, *args, **kwargs):
        if self.orcamento_id and self.orcamento.situacao != SituacaoOrcamento.RASCUNHO:
            raise ValidationError("Itens de uma versão enviada são imutáveis; crie outra versão.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.orcamento.situacao != SituacaoOrcamento.RASCUNHO:
            raise ValidationError("Itens de uma versão enviada são imutáveis.")
        return super().delete(*args, **kwargs)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantidade__gt=0),
                name="item_orcamento_quantidade_maior_que_zero",
            ),
            models.CheckConstraint(
                condition=Q(valor_unitario__gte=0),
                name="item_orcamento_valor_nao_negativo",
            ),
        ]
        verbose_name = "Item de orçamento"
        verbose_name_plural = "Itens de orçamento"


class TipoDecisaoOrcamento(models.TextChoices):
    APROVADO = "APROVADO", "Aprovado"
    RECUSADO = "RECUSADO", "Recusado"


class CanalDecisao(models.TextChoices):
    PRESENCIAL = "PRESENCIAL", "Presencial"
    TELEFONE = "TELEFONE", "Telefone"
    WHATSAPP = "WHATSAPP", "WhatsApp"
    EMAIL = "EMAIL", "E-mail"
    OUTRO = "OUTRO", "Outro"


class DecisaoOrcamento(models.Model):
    orcamento = models.OneToOneField(
        Orcamento,
        on_delete=models.PROTECT,
        related_name="decisao",
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="decisoes_orcamento",
    )
    decisao = models.CharField(max_length=10, choices=TipoDecisaoOrcamento.choices)
    data = models.DateTimeField(default=timezone.now, editable=False)
    canal = models.CharField(max_length=15, choices=CanalDecisao.choices)
    nome_autorizador = models.CharField(max_length=150)
    evidencia = models.ForeignKey(
        "ordens.Anexo",
        on_delete=models.PROTECT,
        related_name="decisoes_comprovadas",
        null=True,
        blank=True,
    )

    def clean(self):
        super().clean()
        if self.evidencia_id and self.orcamento_id:
            if self.evidencia.ordem_id != self.orcamento.ordem_id:
                raise ValidationError({"evidencia": "A evidência precisa pertencer à ordem do orçamento."})
        if self.orcamento_id and self.orcamento.valido_ate and self.orcamento.valido_ate < timezone.localdate():
            raise ValidationError("Não é possível registrar decisão para orçamento expirado.")

    class Meta:
        verbose_name = "Decisão de orçamento"
        verbose_name_plural = "Decisões de orçamento"
