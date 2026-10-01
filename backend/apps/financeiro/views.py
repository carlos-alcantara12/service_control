from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.usuarios.drf_permissions import IsUsuarioAtivo
from apps.usuarios.models import PerfilUsuario

from .models import Pagamento
from .serializers import EstornoCreateSerializer, EstornoSerializer


class PagamentoViewSet(viewsets.GenericViewSet):
    permission_classes = [IsUsuarioAtivo]
    queryset = Pagamento.objects.select_related("ordem", "ordem__tecnico")
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self.request.user, "perfil", None) == PerfilUsuario.TECNICO:
            queryset = queryset.filter(ordem__tecnico=self.request.user)
        return queryset

    @action(detail=True, methods=["post"])
    def estornos(self, request, *args, **kwargs):
        pagamento = self.get_object()
        context = self.get_serializer_context()
        context["pagamento"] = pagamento
        serializer = EstornoCreateSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        estorno = serializer.save()
        return Response(
            EstornoSerializer(
                estorno,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_201_CREATED,
        )
