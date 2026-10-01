from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    ordering = ("nome",)
    list_display = ("nome", "login", "perfil", "ativo", "is_staff")
    list_filter = ("perfil", "ativo", "is_staff")
    search_fields = ("nome", "login", "email")
    fieldsets = (
        (None, {"fields": ("login", "password")} ),
        ("Dados pessoais", {"fields": ("nome", "email", "perfil", "ativo")} ),
        ("Permissões", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")} ),
        ("Datas", {"fields": ("last_login", "date_joined")} ),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("login", "nome", "perfil", "password1", "password2", "ativo", "is_staff"),
        }),
    )
