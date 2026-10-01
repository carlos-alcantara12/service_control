from decimal import Decimal

from rest_framework import serializers


class TecnicoIndicadorSerializer(serializers.Serializer):
    tecnico_id = serializers.IntegerField()
    tecnico_nome = serializers.CharField()
    servicos_concluidos = serializers.IntegerField(min_value=0)


class RelatorioOperacionalSerializer(serializers.Serializer):
    ordens_por_situacao = serializers.DictField(
        child=serializers.IntegerField(min_value=0),
    )
    ordens_atrasadas = serializers.IntegerField(min_value=0)
    tempo_medio_atendimento_dias = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
    )
    servicos_por_tecnico = TecnicoIndicadorSerializer(many=True)
    equipamentos_aguardando_retirada = serializers.IntegerField(min_value=0)
    retornos = serializers.IntegerField(min_value=0)


class RelatorioFinanceiroSerializer(serializers.Serializer):
    orcamentos_aprovados = serializers.IntegerField(min_value=0)
    orcamentos_recusados = serializers.IntegerField(min_value=0)
    valor_aprovado = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0.00"),
    )
    valor_recebido = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0.00"),
    )
    saldo_pendente = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0.00"),
    )
