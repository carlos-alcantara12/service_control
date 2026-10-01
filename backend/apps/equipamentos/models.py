from django.db import models


class Equipamento(models.Model):
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        related_name="equipamentos",
    )
    categoria = models.CharField(max_length=100)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        identificacao = " ".join(filter(None, [self.marca, self.modelo]))
        return f"{identificacao} — {self.cliente.nome}"

    class Meta:
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["cliente", "criado_em"]),
            models.Index(fields=["numero_serie"]),
        ]
        verbose_name = "Equipamento"
        verbose_name_plural = "Equipamentos"
