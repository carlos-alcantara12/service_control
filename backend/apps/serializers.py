from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import PermissionDenied, ValidationError


def convert_service_error(exc):
    if isinstance(exc, DjangoPermissionDenied):
        return PermissionDenied(str(exc))
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            return ValidationError(exc.message_dict)
        return ValidationError(exc.messages)
    return exc


def call_service(function, *args, **kwargs):
    try:
        return function(*args, **kwargs)
    except (DjangoPermissionDenied, DjangoValidationError) as exc:
        raise convert_service_error(exc) from exc


class ServiceActionSerializerMixin:
    def current_user(self):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None:
            raise PermissionDenied("A requisição autenticada é obrigatória.")
        return user

    def current_order(self):
        ordem = self.context.get("ordem")
        if ordem is None:
            raise ValidationError("O contexto da ordem é obrigatório para esta operação.")
        return ordem

    def context_object(self, name):
        value = self.context.get(name)
        if value is None:
            raise ValidationError(f"O contexto de '{name}' é obrigatório para esta operação.")
        return value
