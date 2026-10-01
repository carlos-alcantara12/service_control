from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.auditoria.models import HistoricoAlteracao
from apps.clientes.models import Cliente
from apps.equipamentos.models import Equipamento
from apps.financeiro.models import Estorno, FormaPagamento, Pagamento
from apps.ordens.models import OrdemServico, SituacaoOrdem
from apps.orcamentos.models import (
    ItemOrcamento,
    Orcamento,
    SituacaoOrcamento,
    TipoItemOrcamento,
)
from apps.usuarios.models import PerfilUsuario, Usuario


class ModeloServiceFlowTest(TestCase):
    def setUp(self):
        self.gerente = Usuario.objects.create_user(
            login="gerente",
            password="senha-segura",
            nome="Gerente",
            perfil=PerfilUsuario.GERENTE,
        )
        self.cliente = Cliente.objects.create(
            nome="Cliente de Teste",
            telefone="92999999999",
        )
        self.equipamento = Equipamento.objects.create(
            cliente=self.cliente,
            categoria="Notebook",
            marca="Marca",
            modelo="Modelo",
        )

    def criar_ordem(self):
        return OrdemServico.objects.create(
            cliente=self.cliente,
            equipamento=self.equipamento,
            atendente=self.gerente,
            defeito_relatado="Não liga",
            condicoes_entrada="Sem riscos aparentes",
        )

    def test_ordem_recebe_numero_unico_e_preserva_historico(self):
        ordem = self.criar_ordem()
        self.assertTrue(ordem.numero.startswith("OS-"))
        self.assertEqual(ordem.versao_registro, 1)

        HistoricoAlteracao.objects.create(
            ordem=ordem,
            usuario=self.gerente,
            acao="criada",
            dados_novos={"situacao": SituacaoOrdem.RECEBIDA},
        )
        self.assertEqual(ordem.historico.count(), 1)

    def test_ordem_rejeita_equipamento_de_outro_cliente(self):
        outro_cliente = Cliente.objects.create(nome="Outro", telefone="92000000000")
        outro_equipamento = Equipamento.objects.create(
            cliente=outro_cliente,
            categoria="Celular",
            marca="Marca",
            modelo="Modelo",
        )
        ordem = OrdemServico(
            cliente=self.cliente,
            equipamento=outro_equipamento,
            atendente=self.gerente,
            defeito_relatado="Tela quebrada",
            condicoes_entrada="Com capa",
        )
        with self.assertRaises(ValidationError):
            ordem.full_clean()

    def test_numero_e_versao_bloqueiam_conflitos_de_atualizacao(self):
        ordem = self.criar_ordem()
        numero = ordem.numero
        ordem.numero = "OS-ALTERADA"
        with self.assertRaises(ValidationError):
            ordem.save()

        ordem.refresh_from_db()
        ordem.numero = numero
        ordem.versao_registro = 999
        with self.assertRaises(ValidationError):
            ordem.save()

    def test_orcamento_preserva_versao_e_calcula_total(self):
        ordem = self.criar_ordem()
        orcamento = Orcamento.objects.create(
            ordem=ordem,
            criador=self.gerente,
            versao=1,
        )
        ItemOrcamento.objects.create(
            orcamento=orcamento,
            tipo=TipoItemOrcamento.SERVICO,
            descricao="Diagnóstico",
            quantidade=Decimal("1.000"),
            valor_unitario=Decimal("100.00"),
        )
        ItemOrcamento.objects.create(
            orcamento=orcamento,
            tipo=TipoItemOrcamento.PECA,
            descricao="Peça",
            quantidade=Decimal("2.000"),
            valor_unitario=Decimal("50.00"),
        )
        self.assertEqual(orcamento.total, Decimal("200.000"))

        orcamento.situacao = SituacaoOrcamento.ENVIADO
        orcamento.valido_ate = timezone.localdate() + timedelta(days=7)
        orcamento.save()
        self.assertEqual(Orcamento.objects.filter(ordem=ordem, versao=1).count(), 1)

    def test_estorno_nao_supera_pagamento(self):
        ordem = self.criar_ordem()
        pagamento = Pagamento.objects.create(
            ordem=ordem,
            registrado_por=self.gerente,
            valor=Decimal("100.00"),
            forma=FormaPagamento.PIX,
            identificador_operacao="op-001",
        )
        Estorno.objects.create(
            pagamento=pagamento,
            autorizado_por=self.gerente,
            valor=Decimal("60.00"),
            motivo="Cancelamento parcial",
        )
        estorno_invalido = Estorno(
            pagamento=pagamento,
            autorizado_por=self.gerente,
            valor=Decimal("50.00"),
            motivo="Tentativa acima do limite",
        )
        with self.assertRaises(ValidationError):
            estorno_invalido.full_clean()
