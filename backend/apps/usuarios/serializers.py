from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import PerfilUsuario, Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8,
        validators=[validate_password],
    )
    perfil_display = serializers.CharField(source="get_perfil_display", read_only=True)

    class Meta:
        model = Usuario
        fields = (
            "id",
            "nome",
            "login",
            "email",
            "perfil",
            "perfil_display",
            "ativo",
            "password",
            "date_joined",
        )
        read_only_fields = ("id", "date_joined", "perfil_display")
        extra_kwargs = {
            "nome": {"required": True},
            "login": {"required": True},
            "perfil": {"required": True},
        }

    def validate_perfil(self, value):
        if value not in PerfilUsuario.values:
            raise serializers.ValidationError("Perfil de usuário inválido.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if not password:
            raise serializers.ValidationError({"password": "A senha é obrigatória."})
        return Usuario.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
