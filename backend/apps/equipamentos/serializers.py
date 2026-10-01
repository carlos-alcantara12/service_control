from rest_framework import serializers

from apps.clientes.models import Cliente

from .models import Equipamento


class EquipamentoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source="cliente.nome", read_only=True)

    class Meta:
        model = Equipamento
        fields = (
            "id",
            "cliente",
            "cliente_nome",
            "categoria",
            "marca",
            "modelo",
            "numero_serie",
            "criado_em",
        )
        read_only_fields = ("id", "criado_em", "cliente_nome")
        extra_kwargs = {
            "cliente": {"queryset": Cliente.objects.filter(ativo=True)},
        }

    def validate(self, attrs):
        for field in ("categoria", "marca", "modelo"):
            if not str(attrs.get(field, "")).strip():
                raise serializers.ValidationError({field: "Este campo é obrigatório."})
        return attrs
