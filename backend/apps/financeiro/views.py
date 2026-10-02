from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.usuarios.drf_permissions import IsUsuarioAtivo
from apps.usuarios.models import PerfilUsuario

from .models import Pagamento
from .serializers import EstornoCreateSerializer, EstornoSerializer, PagamentoSerializer


class PagamentoViewSet(viewsets.ModelViewSet):
    queryset = Pagamento.objects.all()
    serializer_class = PagamentoSerializer

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
