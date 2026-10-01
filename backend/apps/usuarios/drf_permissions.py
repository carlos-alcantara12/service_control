from rest_framework.permissions import BasePermission

from .models import PerfilUsuario


class IsUsuarioAtivo(BasePermission):
    message = "É necessário estar autenticado com um usuário ativo."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "ativo", False)
        )


class IsGerente(BasePermission):
    message = "Esta operação exige perfil de gerente."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "ativo", False)
            and request.user.perfil == PerfilUsuario.GERENTE
        )


class IsGerenteOuAtendente(BasePermission):
    message = "Esta operação exige perfil de gerente ou atendente."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "ativo", False)
            and request.user.perfil
            in {PerfilUsuario.GERENTE, PerfilUsuario.ATENDENTE}
        )
