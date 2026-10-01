from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from apps.clientes.models import Cliente
from apps.equipamentos.models import Equipamento
from apps.ordens.models import OrdemServico
from apps.ordens.serializers import OrdemServicoCreateSerializer
from apps.ordens.services import atribuir_tecnico, registrar_diagnostico
from apps.orcamentos.models import TipoItemOrcamento
from apps.orcamentos.serializers import (
    ItemOrcamentoInputSerializer,
    OrcamentoCreateSerializer,
)
from apps.usuarios.models import PerfilUsuario, Usuario


class SerializerTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.atendente = Usuario.objects.create_user(
            login="atendente",
            password="senha-segura",
            nome="Atendente",
            perfil=PerfilUsuario.ATENDENTE,
        )
        self.gerente = Usuario.objects.create_user(
            login="gerente",
            password="senha-segura",
            nome="Gerente",
            perfil=PerfilUsuario.GERENTE,
        )
        self.tecnico = Usuario.objects.create_user(
            login="tecnico",
            password="senha-segura",
            nome="Técnico",
            perfil=PerfilUsuario.TECNICO,
        )
        self.cliente = Cliente.objects.create(nome="Cliente", telefone="92999999999")
        self.equipamento = Equipamento.objects.create(
            cliente=self.cliente,
            categoria="Notebook",
            marca="Marca",
            modelo="Modelo",
        )

    def request_with_user(self, user):
        request = self.factory.post("/api/teste/")
        request.user = user
        return request

    def test_ordem_create_serializer_delega_para_servico(self):
        serializer = OrdemServicoCreateSerializer(
            data={
                "cliente": self.cliente.pk,
                "equipamento": self.equipamento.pk,
                "defeito_relatado": "Não liga",
                "condicoes_entrada": "Sem danos aparentes",
                "previsao_entrega": (timezone.localdate() + timedelta(days=5)).isoformat(),
            },
            context={"request": self.request_with_user(self.atendente)},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        ordem = serializer.save()
        self.assertIsInstance(ordem, OrdemServico)
        self.assertEqual(ordem.atendente_id, self.atendente.pk)

    def test_budget_serializer_delega_criacao_ao_servico(self):
        ordem = OrdemServico.objects.create(
            cliente=self.cliente,
            equipamento=self.equipamento,
            atendente=self.atendente,
            defeito_relatado="Não liga",
            condicoes_entrada="Sem danos aparentes",
        )
        atribuir_tecnico(usuario=self.gerente, ordem=ordem, tecnico=self.tecnico)
        registrar_diagnostico(
            usuario=self.tecnico,
            ordem=ordem,
            diagnostico="Falha na fonte",
        )
        serializer = OrcamentoCreateSerializer(
            data={
                "itens": [
                    {
                        "tipo": TipoItemOrcamento.SERVICO,
                        "descricao": "Reparo",
                        "quantidade": "1.000",
                        "valor_unitario": "120.00",
                    }
                ],
                "valido_ate": (timezone.localdate() + timedelta(days=7)).isoformat(),
            },
            context={
                "request": self.request_with_user(self.tecnico),
                "ordem": ordem,
            },
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        orcamento = serializer.save()
        self.assertEqual(orcamento.itens.count(), 1)

    def test_item_serializer_rejeita_valor_negativo(self):
        serializer = ItemOrcamentoInputSerializer(
            data={
                "tipo": TipoItemOrcamento.PECA,
                "descricao": "Peça inválida",
                "quantidade": "1.000",
                "valor_unitario": "-1.00",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("valor_unitario", serializer.errors)
