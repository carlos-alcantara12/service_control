from django.conf import settings
from django.db import models
from django.utils import timezone


class HistoricoAlteracao(models.Model):
    ordem = models.ForeignKey(
        "ordens.OrdemServico",
        on_delete=models.PROTECT,
        related_name="historico",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="alteracoes_registradas",
        null=True,
        blank=True,
    )
    acao = models.CharField(max_length=100)
    dados_anteriores = models.JSONField(null=True, blank=True)
    dados_novos = models.JSONField(null=True, blank=True)
    justificativa = models.TextField(blank=True)
    registrado_em = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["-registrado_em"]
        indexes = [
            models.Index(fields=["ordem", "registrado_em"]),
            models.Index(fields=["usuario", "registrado_em"]),
        ]
        verbose_name = "Histórico de alteração"
        verbose_name_plural = "Histórico de alterações"
