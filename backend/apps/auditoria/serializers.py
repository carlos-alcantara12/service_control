from rest_framework import serializers

from .models import HistoricoAlteracao


class HistoricoAlteracaoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source="usuario.nome", read_only=True)

    class Meta:
        model = HistoricoAlteracao
        fields = (
            "id",
            "ordem",
            "usuario",
            "usuario_nome",
            "acao",
            "dados_anteriores",
            "dados_novos",
            "justificativa",
            "registrado_em",
        )
        read_only_fields = fields
