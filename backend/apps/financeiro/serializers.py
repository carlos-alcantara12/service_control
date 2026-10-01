from decimal import Decimal

from rest_framework import serializers

from apps.serializers import ServiceActionSerializerMixin, call_service

from .models import (
    Cancelamento,
    Estorno,
    FormaPagamento,
    Pagamento,
    SituacaoPagamento,
    TratamentoFinanceiroCancelamento,
)
from .services import cancelar_ordem, registrar_estorno, registrar_pagamento


class EstornoSerializer(serializers.ModelSerializer):
    autorizado_por_nome = serializers.CharField(source="autorizado_por.nome", read_only=True)

    class Meta:
        model = Estorno
        fields = (
            "id",
            "pagamento",
            "autorizado_por",
            "autorizado_por_nome",
            "valor",
            "motivo",
            "registrado_em",
        )
        read_only_fields = fields


class PagamentoSerializer(serializers.ModelSerializer):
    registrado_por_nome = serializers.CharField(source="registrado_por.nome", read_only=True)
    situacao_display = serializers.CharField(source="get_situacao_display", read_only=True)
    forma_display = serializers.CharField(source="get_forma_display", read_only=True)
    estornos = EstornoSerializer(many=True, read_only=True)

    class Meta:
        model = Pagamento
        fields = (
            "id",
            "ordem",
            "registrado_por",
            "registrado_por_nome",
            "valor",
            "forma",
            "forma_display",
            "situacao",
            "situacao_display",
            "pago_em",
            "referencia",
            "identificador_operacao",
            "estornos",
        )
        read_only_fields = fields


class PagamentoCreateSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    valor = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    forma = serializers.ChoiceField(choices=FormaPagamento.choices)
    situacao = serializers.ChoiceField(
        choices=SituacaoPagamento.choices,
        required=False,
        default=SituacaoPagamento.CONFIRMADO,
    )
    pago_em = serializers.DateTimeField(required=False, allow_null=True)
    referencia = serializers.CharField(required=False, allow_blank=True)
    identificador_operacao = serializers.CharField()

    def create(self, validated_data):
        return call_service(
            registrar_pagamento,
            usuario=self.current_user(),
            ordem=self.current_order(),
            **validated_data,
        )


class EstornoCreateSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    valor = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    motivo = serializers.CharField()

    def create(self, validated_data):
        return call_service(
            registrar_estorno,
            usuario=self.current_user(),
            pagamento=self.context_object("pagamento"),
            **validated_data,
        )


class CancelamentoSerializer(serializers.ModelSerializer):
    responsavel_nome = serializers.CharField(source="responsavel.nome", read_only=True)
    tratamento_financeiro_display = serializers.CharField(
        source="get_tratamento_financeiro_display",
        read_only=True,
    )

    class Meta:
        model = Cancelamento
        fields = (
            "id",
            "ordem",
            "responsavel",
            "responsavel_nome",
            "motivo",
            "tratamento_financeiro",
            "tratamento_financeiro_display",
            "registrado_em",
        )
        read_only_fields = fields


class CancelamentoCreateSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    motivo = serializers.CharField()
    tratamento_financeiro = serializers.ChoiceField(
        choices=TratamentoFinanceiroCancelamento.choices,
    )

    def create(self, validated_data):
        return call_service(
            cancelar_ordem,
            usuario=self.current_user(),
            ordem=self.current_order(),
            **validated_data,
        )
