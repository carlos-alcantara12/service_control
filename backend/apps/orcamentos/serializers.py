from decimal import Decimal

from rest_framework import serializers

from apps.ordens.models import Anexo
from apps.serializers import ServiceActionSerializerMixin, call_service

from .models import (
    CanalDecisao,
    DecisaoOrcamento,
    ItemOrcamento,
    Orcamento,
    SituacaoOrcamento,
    TipoDecisaoOrcamento,
    TipoItemOrcamento,
)
from .services import criar_orcamento, enviar_orcamento, registrar_decisao_orcamento


class ItemOrcamentoSerializer(serializers.ModelSerializer):
    total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = ItemOrcamento
        fields = (
            "id",
            "tipo",
            "tipo_display",
            "descricao",
            "quantidade",
            "valor_unitario",
            "total",
        )
        read_only_fields = ("id", "tipo_display", "total")


class ItemOrcamentoInputSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=TipoItemOrcamento.choices)
    descricao = serializers.CharField()
    quantidade = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.001"),
    )
    valor_unitario = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
    )


class DecisaoOrcamentoSerializer(serializers.ModelSerializer):
    registrado_por_nome = serializers.CharField(source="registrado_por.nome", read_only=True)
    decisao_display = serializers.CharField(source="get_decisao_display", read_only=True)
    canal_display = serializers.CharField(source="get_canal_display", read_only=True)
    evidencia_nome = serializers.CharField(source="evidencia.nome", read_only=True)

    class Meta:
        model = DecisaoOrcamento
        fields = (
            "id",
            "orcamento",
            "registrado_por",
            "registrado_por_nome",
            "decisao",
            "decisao_display",
            "data",
            "canal",
            "canal_display",
            "nome_autorizador",
            "evidencia",
            "evidencia_nome",
        )
        read_only_fields = fields


class OrcamentoSerializer(serializers.ModelSerializer):
    criador_nome = serializers.CharField(source="criador.nome", read_only=True)
    situacao_display = serializers.CharField(source="get_situacao_display", read_only=True)
    total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    itens = ItemOrcamentoSerializer(many=True, read_only=True)
    decisao = serializers.SerializerMethodField()

    class Meta:
        model = Orcamento
        fields = (
            "id",
            "ordem",
            "criador",
            "criador_nome",
            "versao",
            "situacao",
            "situacao_display",
            "criado_em",
            "enviado_em",
            "valido_ate",
            "observacoes",
            "total",
            "itens",
            "decisao",
        )
        read_only_fields = fields

    def get_decisao(self, obj):
        try:
            decisao = obj.decisao
        except DecisaoOrcamento.DoesNotExist:
            decisao = None
        return (
            DecisaoOrcamentoSerializer(decisao, context=self.context).data
            if decisao
            else None
        )


class OrcamentoCreateSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    itens = ItemOrcamentoInputSerializer(many=True, required=False)
    observacoes = serializers.CharField(required=False, allow_blank=True)
    valido_ate = serializers.DateField(required=False, allow_null=True)

    def create(self, validated_data):
        return call_service(
            criar_orcamento,
            usuario=self.current_user(),
            ordem=self.current_order(),
            **validated_data,
        )


class OrcamentoEnviarSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    valido_ate = serializers.DateField(required=False, allow_null=True)

    def create(self, validated_data):
        return call_service(
            enviar_orcamento,
            usuario=self.current_user(),
            orcamento=self.context_object("orcamento"),
            **validated_data,
        )


class DecisaoOrcamentoCreateSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    decisao = serializers.ChoiceField(choices=TipoDecisaoOrcamento.choices)
    canal = serializers.ChoiceField(choices=CanalDecisao.choices)
    nome_autorizador = serializers.CharField()
    evidencia = serializers.PrimaryKeyRelatedField(
        queryset=Anexo.objects.all(),
        required=False,
        allow_null=True,
    )

    def create(self, validated_data):
        return call_service(
            registrar_decisao_orcamento,
            usuario=self.current_user(),
            orcamento=self.context_object("orcamento"),
            **validated_data,
        )
