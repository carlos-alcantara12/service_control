from datetime import date, datetime
from decimal import Decimal

from .models import HistoricoAlteracao


def serializar_valor(valor):
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return str(valor)
    return valor


def snapshot_ordem(ordem):
    return {
        "id": ordem.pk,
        "numero": ordem.numero,
        "cliente_id": ordem.cliente_id,
        "equipamento_id": ordem.equipamento_id,
        "atendente_id": ordem.atendente_id,
        "tecnico_id": ordem.tecnico_id,
        "ordem_original_id": ordem.ordem_original_id,
        "situacao": ordem.situacao,
        "situacao_financeira": ordem.situacao_financeira,
        "prioridade": ordem.prioridade,
        "diagnostico": ordem.diagnostico,
        "previsao_entrega": serializar_valor(ordem.previsao_entrega),
        "conclusao_em": serializar_valor(ordem.conclusao_em),
        "versao_registro": ordem.versao_registro,
    }


def registrar_historico(
    *,
    ordem,
    usuario,
    acao,
    dados_anteriores=None,
    dados_novos=None,
    justificativa="",
):
    return HistoricoAlteracao.objects.create(
        ordem=ordem,
        usuario=usuario,
        acao=acao,
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
        justificativa=justificativa,
    )
