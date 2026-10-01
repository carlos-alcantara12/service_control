from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.equipamentos.models import Equipamento
from apps.financeiro.models import (
    FormaPagamento,
    SituacaoPagamento,
    TratamentoFinanceiroCancelamento,
)
from apps.financeiro.services import (
    cancelar_ordem,
    registrar_estorno,
    registrar_pagamento,
)
from apps.ordens.models import OrdemServico, SituacaoOrdem
from apps.ordens.services import (
    abrir_ordem,
    atribuir_tecnico,
    concluir_testes,
    iniciar_reparo,
    registrar_diagnostico,
    registrar_entrega,
)
from apps.orcamentos.models import CanalDecisao, TipoDecisaoOrcamento, TipoItemOrcamento
from apps.orcamentos.services import (
    criar_orcamento,
    enviar_orcamento,
    registrar_decisao_orcamento,
)
from apps.usuarios.models import PerfilUsuario, Usuario


class ServicesTestCase(TestCase):
    def setUp(self):
        self.gerente = Usuario.objects.create_user(
            login="gerente",
            password="senha",
            nome="Gerente",
            perfil=PerfilUsuario.GERENTE,
        )
        self.atendente = Usuario.objects.create_user(
            login="atendente",
            password="senha",
            nome="Atendente",
            perfil=PerfilUsuario.ATENDENTE,
        )
        self.tecnico = Usuario.objects.create_user(
            login="tecnico",
            password="senha",
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

    def abrir_e_atribuir(self):
        ordem = abrir_ordem(
            atendente=self.atendente,
            cliente=self.cliente,
            equipamento=self.equipamento,
            defeito_relatado="Não liga",
            condicoes_entrada="Sem danos aparentes",
            previsao_entrega=timezone.localdate() + timedelta(days=5),
        )
        atribuir_tecnico(usuario=self.gerente, ordem=ordem, tecnico=self.tecnico)
        return ordem

    def preparar_orcamento_enviado(self):
        ordem = self.abrir_e_atribuir()
        registrar_diagnostico(
            usuario=self.tecnico,
            ordem=ordem,
            diagnostico="Falha na fonte de alimentação",
        )
        orcamento = criar_orcamento(
            usuario=self.tecnico,
            ordem=ordem,
            itens=[
                {
                    "tipo": TipoItemOrcamento.SERVICO,
                    "descricao": "Reparo da fonte",
                    "quantidade": "1",
                    "valor_unitario": "100.00",
                }
            ],
            valido_ate=timezone.localdate() + timedelta(days=7),
        )
        enviar_orcamento(usuario=self.tecnico, orcamento=orcamento)
        return ordem, orcamento

    def aprovar_orcamento(self):
        ordem, orcamento = self.preparar_orcamento_enviado()
        registrar_decisao_orcamento(
            usuario=self.atendente,
            orcamento=orcamento,
            decisao=TipoDecisaoOrcamento.APROVADO,
            canal=CanalDecisao.WHATSAPP,
            nome_autorizador="Cliente",
        )
        return ordem, orcamento

    def test_fluxo_critico_ate_entrega(self):
        ordem, orcamento = self.aprovar_orcamento()
        iniciar_reparo(usuario=self.tecnico, ordem=ordem)
        concluir_testes(
            usuario=self.tecnico,
            ordem=ordem,
            resultado="Equipamento ligado e testado por 30 minutos.",
            aprovado=True,
        )
        registrar_pagamento(
            usuario=self.atendente,
            ordem=ordem,
            valor=Decimal("100.00"),
            forma=FormaPagamento.PIX,
            identificador_operacao="pix-001",
        )
        entrega = registrar_entrega(
            usuario=self.atendente,
            ordem=ordem,
            recebedor="Cliente",
            identificacao="RG-123",
        )
        ordem.refresh_from_db()
        orcamento.refresh_from_db()
        self.assertEqual(orcamento.situacao, "APROVADO")
        self.assertEqual(ordem.situacao, SituacaoOrdem.ENTREGUE)
        self.assertEqual(entrega.ordem_id, ordem.pk)

    def test_reparo_sem_aprovacao_e_bloqueado(self):
        ordem = self.abrir_e_atribuir()
        registrar_diagnostico(
            usuario=self.tecnico,
            ordem=ordem,
            diagnostico="Diagnóstico registrado",
        )
        with self.assertRaises(ValidationError):
            iniciar_reparo(usuario=self.tecnico, ordem=ordem)

    def test_tecnico_nao_pode_registrar_decisao(self):
        ordem, orcamento = self.preparar_orcamento_enviado()
        with self.assertRaises(PermissionDenied):
            registrar_decisao_orcamento(
                usuario=self.tecnico,
                orcamento=orcamento,
                decisao=TipoDecisaoOrcamento.APROVADO,
                canal=CanalDecisao.PRESENCIAL,
                nome_autorizador="Cliente",
            )

    def test_estorno_exige_gerente_e_respeita_limite(self):
        ordem, _ = self.aprovar_orcamento()
        pagamento = registrar_pagamento(
            usuario=self.atendente,
            ordem=ordem,
            valor=Decimal("100.00"),
            forma=FormaPagamento.DINHEIRO,
            identificador_operacao="dinheiro-001",
        )
        with self.assertRaises(PermissionDenied):
            registrar_estorno(
                usuario=self.atendente,
                pagamento=pagamento,
                valor=Decimal("10.00"),
                motivo="Devolução",
            )
        with self.assertRaises(ValidationError):
            registrar_estorno(
                usuario=self.gerente,
                pagamento=pagamento,
                valor=Decimal("100.01"),
                motivo="Devolução",
            )

    def test_entrega_com_saldo_exige_excecao_de_gerente(self):
        ordem, _ = self.aprovar_orcamento()
        iniciar_reparo(usuario=self.tecnico, ordem=ordem)
        concluir_testes(
            usuario=self.tecnico,
            ordem=ordem,
            resultado="Teste aprovado",
            aprovado=True,
        )
        with self.assertRaises(ValidationError):
            registrar_entrega(
                usuario=self.atendente,
                ordem=ordem,
                recebedor="Cliente",
            )
        entrega = registrar_entrega(
            usuario=self.atendente,
            ordem=ordem,
            recebedor="Cliente",
            autorizacao_excecao_por=self.gerente,
        )
        self.assertEqual(entrega.autorizacao_excecao_por_id, self.gerente.pk)

    def test_cancelamento_preserva_ordem_e_historico(self):
        ordem = self.abrir_e_atribuir()
        cancelamento = cancelar_ordem(
            usuario=self.atendente,
            ordem=ordem,
            motivo="Cliente desistiu",
            tratamento_financeiro=TratamentoFinanceiroCancelamento.SEM_COBRANCA,
        )
        ordem.refresh_from_db()
        self.assertEqual(ordem.situacao, SituacaoOrdem.CANCELADA)
        self.assertEqual(cancelamento.ordem_id, ordem.pk)
        self.assertTrue(ordem.historico.filter(acao="ordem_cancelada").exists())
