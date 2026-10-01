from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class PerfilUsuario(models.TextChoices):
    GERENTE = "GERENTE", "Gerente"
    ATENDENTE = "ATENDENTE", "Atendente"
    TECNICO = "TECNICO", "Técnico"


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, login, password=None, **extra_fields):
        if not login:
            raise ValueError("O login é obrigatório.")
        usuario = self.model(login=login.strip().lower(), **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, login, password=None, **extra_fields):
        extra_fields.setdefault("perfil", PerfilUsuario.GERENTE)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("ativo", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuário precisa de is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuário precisa de is_superuser=True.")
        return self.create_user(login, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    nome = models.CharField(max_length=150)
    login = models.CharField(max_length=150, unique=True)
    email = models.EmailField(blank=True)
    perfil = models.CharField(max_length=20, choices=PerfilUsuario.choices)
    ativo = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "login"
    REQUIRED_FIELDS = ["nome"]

    @property
    def is_active(self):
        return self.ativo

    def __str__(self):
        return f"{self.nome} ({self.login})"

    class Meta:
        ordering = ["nome"]
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
