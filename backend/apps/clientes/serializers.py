from rest_framework import serializers

from .models import Cliente


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = (
            "id",
            "nome",
            "telefone",
            "email",
            "documento",
            "endereco",
            "criado_em",
            "ativo",
        )
        read_only_fields = ("id", "criado_em")

    def validate_nome(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("O nome é obrigatório.")
        return value

    def validate_telefone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("O telefone é obrigatório.")
        return value
