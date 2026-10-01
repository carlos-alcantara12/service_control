from django.core.exceptions import PermissionDenied

from .models import PerfilUsuario


def exigir_usuario_ativo(usuario):
    if not usuario or not getattr(usuario, "is_authenticated", False):
        raise PermissionDenied("É necessário estar autenticado.")
    if not getattr(usuario, "ativo", False):
        raise PermissionDenied("O usuário está inativo.")
    return usuario


def exigir_perfil(usuario, *perfis):
    usuario = exigir_usuario_ativo(usuario)
    if usuario.perfil not in perfis:
        nomes = ", ".join(str(perfil) for perfil in perfis)
        raise PermissionDenied(f"A operação exige um destes perfis: {nomes}.")
    return usuario


def exigir_gerente(usuario):
    return exigir_perfil(usuario, PerfilUsuario.GERENTE)


def exigir_gerente_ou_atendente(usuario):
    return exigir_perfil(
        usuario,
        PerfilUsuario.GERENTE,
        PerfilUsuario.ATENDENTE,
    )


def exigir_tecnico_da_ordem(usuario, ordem):
    usuario = exigir_usuario_ativo(usuario)
    if usuario.perfil == PerfilUsuario.GERENTE:
        return usuario
    if usuario.perfil != PerfilUsuario.TECNICO or ordem.tecnico_id != usuario.pk:
        raise PermissionDenied("O técnico só pode operar ordens atribuídas a ele.")
    return usuario


def exigir_tecnico_ou_gerente(usuario, ordem):
    return exigir_tecnico_da_ordem(usuario, ordem)
