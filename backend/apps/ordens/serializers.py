from decimal import Decimal

from rest_framework import serializers

from apps.clientes.models import Cliente
from apps.equipamentos.models import Equipamento
from apps.serializers import ServiceActionSerializerMixin, call_service
from apps.usuarios.models import PerfilUsuario, Usuario

from .models import (
    Anexo,
    AtividadeServico,
    CategoriaAnexo,
    Entrega,
    OrdemServico,
    PecaUtilizada,
    PrioridadeOrdem,
    SituacaoOrdem,
    TipoAtividade,
)
from .services import (
    abrir_ordem,
    abrir_retorno,
    alterar_prazo,
    atribuir_tecnico,
    concluir_testes,
    iniciar_reparo,
    registrar_atividade,
    registrar_diagnostico,
    registrar_entrega,
    registrar_peca_utilizada,
)


class AtividadeServicoSerializer(serializers.ModelSerializer):
    tecnico_nome = serializers.CharField(source="tecnico.nome", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = AtividadeServico
        fields = (
            "id",
            "tecnico",
            "tecnico_nome",
            "tipo",
            "tipo_display",
            "descricao",
            "registrado_em",
            "resultado",
        )
        read_only_fields = ("id", "tecnico", "tecnico_nome", "registrado_em", "tipo_display")


class PecaUtilizadaSerializer(serializers.ModelSerializer):
    registrado_por_nome = serializers.CharField(source="registrado_por.nome", read_only=True)
    custo_total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = PecaUtilizada
        fields = (
            "id",
            "registrado_por",
            "registrado_por_nome",
            "descricao",
            "quantidade",
            "custo_unitario",
            "custo_total",
            "utilizada_em",
        )
        read_only_fields = (
            "id",
            "registrado_por",
            "registrado_por_nome",
            "custo_total",
            "utilizada_em",
        )


class AnexoSerializer(serializers.ModelSerializer):
    enviado_por_nome = serializers.CharField(source="enviado_por.nome", read_only=True)
    categoria_display = serializers.CharField(source="get_categoria_display", read_only=True)

    class Meta:
        model = Anexo
        fields = (
            "id",
            "nome",
            "caminho",
            "tipo",
            "tamanho",
            "categoria",
            "categoria_display",
            "enviado_por",
            "enviado_por_nome",
            "enviado_em",
        )
        read_only_fields = fields


class AnexoUploadSerializer(ServiceActionSerializerMixin, serializers.ModelSerializer):
    nome = serializers.CharField(required=False, allow_blank=True)
    caminho = serializers.FileField(write_only=True)
    tamanho = serializers.IntegerField(read_only=True)
    tipo = serializers.CharField(read_only=True)

    MAX_SIZE = 10 * 1024 * 1024
    ALLOWED_TYPES = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "text/plain",
    }

    class Meta:
        model = Anexo
        fields = ("id", "nome", "caminho", "tipo", "tamanho", "categoria", "enviado_em")
        read_only_fields = ("id", "tipo", "tamanho", "enviado_em")

    def validate_categoria(self, value):
        if value not in CategoriaAnexo.values:
            raise serializers.ValidationError("Categoria de anexo inválida.")
        return value

    def validate_caminho(self, arquivo):
        if arquivo.size <= 0:
            raise serializers.ValidationError("O arquivo não pode estar vazio.")
        if arquivo.size > self.MAX_SIZE:
            raise serializers.ValidationError("O arquivo não pode ultrapassar 10 MB.")
        content_type = getattr(arquivo, "content_type", None)
        if content_type and content_type not in self.ALLOWED_TYPES:
            raise serializers.ValidationError("Tipo de arquivo não permitido.")
        return arquivo

    def create(self, validated_data):
        arquivo = validated_data["caminho"]
        ordem = self.current_order()
        usuario = self.current_user()
        anexo = Anexo(
            ordem=ordem,
            enviado_por=usuario,
            nome=(validated_data.get("nome") or arquivo.name).strip(),
            caminho=arquivo,
            tipo=getattr(arquivo, "content_type", "") or "application/octet-stream",
            tamanho=arquivo.size,
            categoria=validated_data["categoria"],
        )
        anexo.full_clean()
        anexo.save()
        return anexo


class OrdemServicoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source="cliente.nome", read_only=True)
    equipamento_descricao = serializers.SerializerMethodField()
    atendente_nome = serializers.CharField(source="atendente.nome", read_only=True)
    tecnico_nome = serializers.CharField(source="tecnico.nome", read_only=True)
    ordem_original_numero = serializers.CharField(source="ordem_original.numero", read_only=True)
    situacao_display = serializers.CharField(source="get_situacao_display", read_only=True)
    situacao_financeira_display = serializers.CharField(
        source="get_situacao_financeira_display",
        read_only=True,
    )
    prioridade_display = serializers.CharField(source="get_prioridade_display", read_only=True)
    valor_aprovado = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    saldo_pendente = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = OrdemServico
        fields = (
            "id",
            "numero",
            "cliente",
            "cliente_nome",
            "equipamento",
            "equipamento_descricao",
            "atendente",
            "atendente_nome",
            "tecnico",
            "tecnico_nome",
            "ordem_original",
            "ordem_original_numero",
            "defeito_relatado",
            "condicoes_entrada",
            "acessorios",
            "diagnostico",
            "situacao",
            "situacao_display",
            "situacao_financeira",
            "situacao_financeira_display",
            "prioridade",
            "prioridade_display",
            "entrada_em",
            "previsao_entrega",
            "conclusao_em",
            "versao_registro",
            "valor_aprovado",
            "saldo_pendente",
        )
        read_only_fields = fields

    def get_equipamento_descricao(self, obj):
        return str(obj.equipamento)


class OrdemServicoDetalheSerializer(OrdemServicoSerializer):
    orcamentos = serializers.SerializerMethodField()
    atividades = serializers.SerializerMethodField()
    pecas_utilizadas = serializers.SerializerMethodField()
    pagamentos = serializers.SerializerMethodField()
    anexos = serializers.SerializerMethodField()
    historico = serializers.SerializerMethodField()
    entrega = serializers.SerializerMethodField()
    cancelamento = serializers.SerializerMethodField()

    class Meta(OrdemServicoSerializer.Meta):
        fields = OrdemServicoSerializer.Meta.fields + (
            "orcamentos",
            "atividades",
            "pecas_utilizadas",
            "pagamentos",
            "anexos",
            "historico",
            "entrega",
            "cancelamento",
        )

    def get_orcamentos(self, obj):
        from apps.orcamentos.serializers import OrcamentoSerializer

        return OrcamentoSerializer(obj.orcamentos.all(), many=True, context=self.context).data

    def get_atividades(self, obj):
        return AtividadeServicoSerializer(obj.atividades.all(), many=True, context=self.context).data

    def get_pecas_utilizadas(self, obj):
        return PecaUtilizadaSerializer(obj.pecas_utilizadas.all(), many=True, context=self.context).data

    def get_pagamentos(self, obj):
        from apps.financeiro.serializers import PagamentoSerializer

        return PagamentoSerializer(obj.pagamentos.all(), many=True, context=self.context).data

    def get_anexos(self, obj):
        return AnexoSerializer(obj.anexos.all(), many=True, context=self.context).data

    def get_historico(self, obj):
        from apps.auditoria.serializers import HistoricoAlteracaoSerializer

        return HistoricoAlteracaoSerializer(obj.historico.all(), many=True, context=self.context).data

    def get_entrega(self, obj):
        entrega = getattr(obj, "entrega", None)
        return EntregaSerializer(entrega, context=self.context).data if entrega else None

    def get_cancelamento(self, obj):
        cancelamento = getattr(obj, "cancelamento", None)
        if not cancelamento:
            return None
        from apps.financeiro.serializers import CancelamentoSerializer

        return CancelamentoSerializer(cancelamento, context=self.context).data


class OrdemServicoCreateSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    cliente = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.filter(ativo=True))
    equipamento = serializers.PrimaryKeyRelatedField(queryset=Equipamento.objects.all())
    defeito_relatado = serializers.CharField()
    condicoes_entrada = serializers.CharField()
    acessorios = serializers.CharField(required=False, allow_blank=True)
    prioridade = serializers.ChoiceField(choices=PrioridadeOrdem.choices, required=False)
    previsao_entrega = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs["equipamento"].cliente_id != attrs["cliente"].pk:
            raise serializers.ValidationError(
                {"equipamento": "O equipamento precisa pertencer ao cliente informado."}
            )
        return attrs

    def create(self, validated_data):
        return call_service(
            abrir_ordem,
            atendente=self.current_user(),
            **validated_data,
        )


class AtribuirTecnicoSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    tecnico = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(perfil=PerfilUsuario.TECNICO, ativo=True),
    )

    def create(self, validated_data):
        return call_service(
            atribuir_tecnico,
            usuario=self.current_user(),
            ordem=self.current_order(),
            tecnico=validated_data["tecnico"],
        )


class DiagnosticoSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    diagnostico = serializers.CharField()

    def create(self, validated_data):
        return call_service(
            registrar_diagnostico,
            usuario=self.current_user(),
            ordem=self.current_order(),
            diagnostico=validated_data["diagnostico"],
        )


class AtividadeCreateSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    tipo = serializers.ChoiceField(choices=TipoAtividade.choices)
    descricao = serializers.CharField()
    resultado = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        return call_service(
            registrar_atividade,
            usuario=self.current_user(),
            ordem=self.current_order(),
            **validated_data,
        )


class PecaUtilizadaCreateSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    descricao = serializers.CharField()
    quantidade = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))
    custo_unitario = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.00"))

    def create(self, validated_data):
        return call_service(
            registrar_peca_utilizada,
            usuario=self.current_user(),
            ordem=self.current_order(),
            **validated_data,
        )


class AlterarPrazoSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    previsao_entrega = serializers.DateField()
    justificativa = serializers.CharField()

    def create(self, validated_data):
        return call_service(
            alterar_prazo,
            usuario=self.current_user(),
            ordem=self.current_order(),
            **validated_data,
        )


class IniciarReparoSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    def create(self, validated_data):
        return call_service(
            iniciar_reparo,
            usuario=self.current_user(),
            ordem=self.current_order(),
        )


class ConcluirTestesSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    resultado = serializers.CharField()
    aprovado = serializers.BooleanField()

    def create(self, validated_data):
        return call_service(
            concluir_testes,
            usuario=self.current_user(),
            ordem=self.current_order(),
            **validated_data,
        )


class EntregaSerializer(serializers.ModelSerializer):
    funcionario_nome = serializers.CharField(source="funcionario.nome", read_only=True)
    autorizacao_excecao_por_nome = serializers.CharField(
        source="autorizacao_excecao_por.nome",
        read_only=True,
    )

    class Meta:
        model = Entrega
        fields = (
            "id",
            "ordem",
            "funcionario",
            "funcionario_nome",
            "recebedor",
            "identificacao",
            "entregue_em",
            "comprovante",
            "observacoes",
            "autorizacao_excecao_por",
            "autorizacao_excecao_por_nome",
        )
        read_only_fields = fields


class EntregaCreateSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    recebedor = serializers.CharField()
    identificacao = serializers.CharField(required=False, allow_blank=True)
    comprovante = serializers.PrimaryKeyRelatedField(
        queryset=Anexo.objects.all(),
        required=False,
        allow_null=True,
    )
    observacoes = serializers.CharField(required=False, allow_blank=True)
    autorizacao_excecao_por = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(perfil=PerfilUsuario.GERENTE, ativo=True),
        required=False,
        allow_null=True,
    )

    def create(self, validated_data):
        return call_service(
            registrar_entrega,
            usuario=self.current_user(),
            ordem=self.current_order(),
            **validated_data,
        )


class RetornoCreateSerializer(ServiceActionSerializerMixin, serializers.Serializer):
    defeito_relatado = serializers.CharField()
    condicoes_entrada = serializers.CharField()
    acessorios = serializers.CharField(required=False, allow_blank=True)
    prioridade = serializers.ChoiceField(choices=PrioridadeOrdem.choices, required=False)
    previsao_entrega = serializers.DateField(required=False, allow_null=True)

    def create(self, validated_data):
        return call_service(
            abrir_retorno,
            usuario=self.current_user(),
            ordem_original=self.current_order(),
            **validated_data,
        )
