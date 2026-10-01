import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


def gerar_numero_ordem():
    """Gera um identificador de negócio imutável e seguro para uma OS."""
    return f"OS-{uuid.uuid4().hex[:12].upper()}"


class SituacaoOrdem(models.TextChoices):
    RECEBIDA = "RECEBIDA", "Recebida"
    EM_DIAGNOSTICO = "EM_DIAGNOSTICO", "Em diagnóstico"
    AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO", "Aguardando aprovação"
    EM_REPARO = "EM_REPARO", "Em reparo"
    AGUARDANDO_PECA = "AGUARDANDO_PECA", "Aguardando peça"
    EM_TESTES = "EM_TESTES", "Em testes"
    PREPARAR_DEVOLUCAO = "PREPARAR_DEVOLUCAO", "Preparar devolução"
    PRONTA_ENTREGA = "PRONTA_ENTREGA", "Pronta para entrega"
    ENTREGUE = "ENTREGUE", "Entregue"
    CANCELADA = "CANCELADA", "Cancelada"


class PrioridadeOrdem(models.TextChoices):
    BAIXA = "BAIXA", "Baixa"
    NORMAL = "NORMAL", "Normal"
    ALTA = "ALTA", "Alta"
    URGENTE = "URGENTE", "Urgente"


class SituacaoFinanceira(models.TextChoices):
    PENDENTE = "PENDENTE", "Pendente"
    PARCIAL = "PARCIAL", "Parcial"
    QUITADA = "QUITADA", "Quitada"
    ESTORNADA = "ESTORNADA", "Estornada"
    CANCELADA = "CANCELADA", "Cancelada"


class OrdemServico(models.Model):
    numero = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        default=gerar_numero_ordem,
    )
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        related_name="ordens",
    )
    equipamento = models.ForeignKey(
        "equipamentos.Equipamento",
        on_delete=models.PROTECT,
        related_name="ordens",
    )
    atendente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ordens_atendidas",
    )
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ordens_tecnico",
        null=True,
        blank=True,
    )
    ordem_original = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="retornos",
        null=True,
        blank=True,
    )
    defeito_relatado = models.TextField()
    condicoes_entrada = models.TextField()
    acessorios = models.TextField(blank=True)
    diagnostico = models.TextField(blank=True)
    situacao = models.CharField(
        max_length=30,
        choices=SituacaoOrdem.choices,
        default=SituacaoOrdem.RECEBIDA,
    )
    situacao_financeira = models.CharField(
        max_length=20,
        choices=SituacaoFinanceira.choices,
        default=SituacaoFinanceira.PENDENTE,
    )
    prioridade = models.CharField(
        max_length=10,
        choices=PrioridadeOrdem.choices,
        default=PrioridadeOrdem.NORMAL,
    )
    entrada_em = models.DateTimeField(default=timezone.now, editable=False)
    previsao_entrega = models.DateField(null=True, blank=True)
    conclusao_em = models.DateTimeField(null=True, blank=True)
    versao_registro = models.PositiveIntegerField(default=1)

    def clean(self):
        super().clean()
        erros = {}
        if self.equipamento_id and self.cliente_id:
            equipamento_cliente_id = (
                self.equipamento.cliente_id
                if hasattr(self.equipamento, "cliente_id")
                else None
            )
            if equipamento_cliente_id != self.cliente_id:
                erros["equipamento"] = "O equipamento precisa pertencer ao cliente da ordem."
        if self.tecnico_id and not self.tecnico.ativo:
            erros["tecnico"] = "O técnico responsável precisa estar ativo."
        if self.ordem_original_id and self.ordem_original_id == self.pk:
            erros["ordem_original"] = "Uma ordem não pode ser retorno dela mesma."
        if self.ordem_original_id:
            original = self.ordem_original
            if original.cliente_id != self.cliente_id:
                erros["cliente"] = "O retorno precisa manter o cliente da ordem original."
            if original.equipamento_id != self.equipamento_id:
                erros["equipamento"] = "O retorno precisa manter o equipamento da ordem original."
        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        if self.pk:
            atual = type(self).objects.only("numero", "versao_registro").get(pk=self.pk)
            if self.numero != atual.numero:
                raise ValidationError("O número da ordem é imutável.")
            if self.versao_registro != atual.versao_registro:
                raise ValidationError(
                    "A ordem foi alterada por outro usuário; atualize os dados antes de salvar."
                )
            self.versao_registro += 1
            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {"versao_registro"}
        return super().save(*args, **kwargs)

    @property
    def saldo_pendente(self):
        from apps.financeiro.models import Pagamento

        total_pago = Pagamento.total_confirmado_para_ordem(self.pk)
        return max(self.valor_aprovado - total_pago, 0)

    @property
    def valor_aprovado(self):
        orcamento = (
            self.orcamentos.filter(situacao="APROVADO")
            .order_by("-versao")
            .first()
        )
        return orcamento.total if orcamento else 0

    def __str__(self):
        return self.numero

    class Meta:
        ordering = ["-entrada_em"]
        indexes = [
            models.Index(fields=["situacao", "previsao_entrega"]),
            models.Index(fields=["tecnico", "situacao"]),
            models.Index(fields=["cliente", "entrada_em"]),
            models.Index(fields=["equipamento", "entrada_em"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(versao_registro__gte=1),
                name="ordem_versao_registro_positiva",
            ),
        ]
        verbose_name = "Ordem de serviço"
        verbose_name_plural = "Ordens de serviço"


class TipoAtividade(models.TextChoices):
    DIAGNOSTICO = "DIAGNOSTICO", "Diagnóstico"
    REPARO = "REPARO", "Reparo"
    TESTE = "TESTE", "Teste"
    DEVOLUCAO = "DEVOLUCAO", "Devolução"
    OUTRO = "OUTRO", "Outro"


class AtividadeServico(models.Model):
    ordem = models.ForeignKey(
        OrdemServico,
        on_delete=models.PROTECT,
        related_name="atividades",
    )
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="atividades_servico",
    )
    tipo = models.CharField(max_length=20, choices=TipoAtividade.choices)
    descricao = models.TextField()
    registrado_em = models.DateTimeField(default=timezone.now, editable=False)
    resultado = models.TextField(blank=True)

    def clean(self):
        super().clean()
        if self.tecnico_id and not self.tecnico.ativo:
            raise ValidationError({"tecnico": "O técnico precisa estar ativo."})
        if self.tipo == TipoAtividade.TESTE and not self.resultado.strip():
            raise ValidationError({"resultado": "Testes precisam registrar um resultado."})

    class Meta:
        ordering = ["-registrado_em"]
        indexes = [
            models.Index(fields=["ordem", "registrado_em"]),
            models.Index(fields=["tecnico", "registrado_em"]),
        ]
        verbose_name = "Atividade de serviço"
        verbose_name_plural = "Atividades de serviço"


class PecaUtilizada(models.Model):
    ordem = models.ForeignKey(
        OrdemServico,
        on_delete=models.PROTECT,
        related_name="pecas_utilizadas",
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pecas_registradas",
    )
    descricao = models.CharField(max_length=200)
    quantidade = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0.001)],
    )
    custo_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    utilizada_em = models.DateTimeField(default=timezone.now, editable=False)

    @property
    def custo_total(self):
        return self.quantidade * self.custo_unitario

    class Meta:
        ordering = ["-utilizada_em"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantidade__gt=0),
                name="peca_quantidade_maior_que_zero",
            ),
            models.CheckConstraint(
                condition=Q(custo_unitario__gte=0),
                name="peca_custo_nao_negativo",
            ),
        ]
        verbose_name = "Peça utilizada"
        verbose_name_plural = "Peças utilizadas"


class CategoriaAnexo(models.TextChoices):
    ENTRADA = "ENTRADA", "Condições de entrada"
    ORCAMENTO = "ORCAMENTO", "Orçamento"
    EVIDENCIA = "EVIDENCIA", "Evidência"
    COMPROVANTE = "COMPROVANTE", "Comprovante"
    OUTRO = "OUTRO", "Outro"


class Anexo(models.Model):
    ordem = models.ForeignKey(
        OrdemServico,
        on_delete=models.PROTECT,
        related_name="anexos",
    )
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="anexos_enviados",
    )
    nome = models.CharField(max_length=255)
    caminho = models.FileField(upload_to="ordens/anexos/%Y/%m/")
    tipo = models.CharField(max_length=100)
    tamanho = models.PositiveBigIntegerField()
    categoria = models.CharField(max_length=20, choices=CategoriaAnexo.choices)
    enviado_em = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["-enviado_em"]
        indexes = [
            models.Index(fields=["ordem", "categoria"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(tamanho__gt=0),
                name="anexo_tamanho_maior_que_zero",
            ),
        ]
        verbose_name = "Anexo"
        verbose_name_plural = "Anexos"


class Entrega(models.Model):
    ordem = models.OneToOneField(
        OrdemServico,
        on_delete=models.PROTECT,
        related_name="entrega",
    )
    funcionario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="entregas_registradas",
    )
    recebedor = models.CharField(max_length=150)
    identificacao = models.CharField(max_length=100, blank=True)
    entregue_em = models.DateTimeField(default=timezone.now, editable=False)
    comprovante = models.ForeignKey(
        Anexo,
        on_delete=models.PROTECT,
        related_name="entregas_comprovadas",
        null=True,
        blank=True,
    )
    observacoes = models.TextField(blank=True)
    autorizacao_excecao_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="entregas_autorizadas_excepcionalmente",
        null=True,
        blank=True,
    )

    def clean(self):
        super().clean()
        if self.comprovante_id and self.comprovante.ordem_id != self.ordem_id:
            raise ValidationError({"comprovante": "O comprovante precisa pertencer à mesma ordem."})

    class Meta:
        verbose_name = "Entrega"
        verbose_name_plural = "Entregas"
