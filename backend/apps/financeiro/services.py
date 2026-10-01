from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.auditoria.services import registrar_historico, snapshot_ordem
from apps.ordens.models import SituacaoFinanceira, SituacaoOrdem
from apps.ordens.services import _obter_ordem_bloqueada, _salvar_ordem, _mudar_situacao
from apps.usuarios.permissions import exigir_gerente, exigir_gerente_ou_atendente

from .models import (
    Cancelamento,
    Estorno,
    Pagamento,
    SituacaoPagamento,
    TratamentoFinanceiroCancelamento,
)


def _decimal_positivo(valor, campo="valor"):
    try:
        valor = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError({campo: "Informe um valor válido."}) from exc
    if valor <= 0:
        raise ValidationError({campo: "O valor precisa ser maior que zero."})
    return valor


def _recalcular_situacao_financeira(ordem):
    pagamentos = list(Pagamento.objects.filter(ordem=ordem))
    if not pagamentos:
        nova_situacao = SituacaoFinanceira.PENDENTE
    else:
        liquido = Pagamento.total_confirmado_para_ordem(ordem.pk)
        total_aprovado = ordem.valor_aprovado
        possui_pagamento_ativo = any(
            pagamento.situacao in {
                SituacaoPagamento.PENDENTE,
                SituacaoPagamento.CONFIRMADO,
            }
            for pagamento in pagamentos
        )
        possui_estorno = any(
            pagamento.situacao == SituacaoPagamento.ESTORNADO
            for pagamento in pagamentos
        )
        if liquido <= 0 and possui_estorno and not possui_pagamento_ativo:
            nova_situacao = SituacaoFinanceira.ESTORNADA
        elif liquido > 0 and total_aprovado and liquido >= total_aprovado:
            nova_situacao = SituacaoFinanceira.QUITADA
        elif liquido > 0:
            nova_situacao = SituacaoFinanceira.PARCIAL
        else:
            nova_situacao = SituacaoFinanceira.PENDENTE

    if ordem.situacao_financeira != nova_situacao:
        ordem.situacao_financeira = nova_situacao
        _salvar_ordem(ordem, {"situacao_financeira"})
    return ordem


@transaction.atomic
def registrar_pagamento(
    *,
    usuario,
    ordem,
    valor,
    forma,
    identificador_operacao,
    referencia="",
    pago_em=None,
    situacao=SituacaoPagamento.CONFIRMADO,
):
    exigir_gerente_ou_atendente(usuario)
    ordem = _obter_ordem_bloqueada(ordem)
    if ordem.situacao == SituacaoOrdem.CANCELADA:
        raise ValidationError("Não é possível registrar novo pagamento em ordem cancelada.")
    valor = _decimal_positivo(valor)
    identificador_operacao = str(identificador_operacao or "").strip()
    if not identificador_operacao:
        raise ValidationError({"identificador_operacao": "O identificador da operação é obrigatório."})
    if Pagamento.objects.filter(identificador_operacao=identificador_operacao).exists():
        raise ValidationError({"identificador_operacao": "Essa operação já foi registrada."})
    if situacao not in SituacaoPagamento.values:
        raise ValidationError({"situacao": "Situação de pagamento inválida."})

    pagamento = Pagamento(
        ordem=ordem,
        registrado_por=usuario,
        valor=valor,
        forma=forma,
        situacao=situacao,
        referencia=str(referencia or "").strip(),
        identificador_operacao=identificador_operacao,
        pago_em=pago_em or timezone.now(),
    )
    pagamento.full_clean()
    pagamento.save()

    anterior = snapshot_ordem(ordem)
    _recalcular_situacao_financeira(ordem)
    registrar_historico(
        ordem=ordem,
        usuario=usuario,
        acao="pagamento_registrado",
        dados_anteriores=anterior,
        dados_novos={
            **snapshot_ordem(ordem),
            "pagamento_id": pagamento.pk,
            "valor": str(pagamento.valor),
            "forma": pagamento.forma,
            "situacao": pagamento.situacao,
            "identificador_operacao": pagamento.identificador_operacao,
        },
    )
    return pagamento


@transaction.atomic
def registrar_estorno(*, usuario, pagamento, valor, motivo):
    exigir_gerente(usuario)
    pagamento_id = getattr(pagamento, "pk", pagamento)
    pagamento = Pagamento.objects.select_for_update().get(pk=pagamento_id)
    if pagamento.situacao != SituacaoPagamento.CONFIRMADO:
        raise ValidationError("Somente pagamentos confirmados podem ser estornados.")
    valor = _decimal_positivo(valor)
    motivo = str(motivo or "").strip()
    if not motivo:
        raise ValidationError({"motivo": "O motivo do estorno é obrigatório."})

    total_estornado = sum(
        (estorno.valor for estorno in pagamento.estornos.all()),
        Decimal("0.00"),
    )
    if total_estornado + valor > pagamento.valor:
        raise ValidationError({"valor": "A soma dos estornos não pode superar o pagamento."})

    estorno = Estorno(
        pagamento=pagamento,
        autorizado_por=usuario,
        valor=valor,
        motivo=motivo,
    )
    estorno.full_clean()
    estorno.save()
    total_estornado += valor
    if total_estornado == pagamento.valor:
        pagamento.situacao = SituacaoPagamento.ESTORNADO
        pagamento.save(update_fields={"situacao"})

    ordem = _obter_ordem_bloqueada(pagamento.ordem)
    anterior = snapshot_ordem(ordem)
    _recalcular_situacao_financeira(ordem)
    registrar_historico(
        ordem=ordem,
        usuario=usuario,
        acao="estorno_registrado",
        dados_anteriores=anterior,
        dados_novos={
            **snapshot_ordem(ordem),
            "estorno_id": estorno.pk,
            "pagamento_id": pagamento.pk,
            "valor": str(estorno.valor),
            "motivo": estorno.motivo,
        },
    )
    return estorno


@transaction.atomic
def cancelar_ordem(*, usuario, ordem, motivo, tratamento_financeiro):
    exigir_gerente_ou_atendente(usuario)
    ordem = _obter_ordem_bloqueada(ordem)
    if ordem.situacao in {SituacaoOrdem.ENTREGUE, SituacaoOrdem.CANCELADA}:
        raise ValidationError("A ordem já está encerrada e não pode ser cancelada novamente.")
    if Cancelamento.objects.filter(ordem=ordem).exists():
        raise ValidationError("Já existe cancelamento registrado para esta ordem.")
    motivo = str(motivo or "").strip()
    if not motivo:
        raise ValidationError({"motivo": "O motivo do cancelamento é obrigatório."})
    if tratamento_financeiro not in TratamentoFinanceiroCancelamento.values:
        raise ValidationError({"tratamento_financeiro": "Tratamento financeiro inválido."})

    cancelamento = Cancelamento(
        ordem=ordem,
        responsavel=usuario,
        motivo=motivo,
        tratamento_financeiro=tratamento_financeiro,
    )
    cancelamento.full_clean()
    cancelamento.save()

    anterior = snapshot_ordem(ordem)
    _mudar_situacao(ordem, SituacaoOrdem.CANCELADA)
    possui_pagamento_ativo = Pagamento.objects.filter(
        ordem=ordem,
    ).exclude(situacao=SituacaoPagamento.ESTORNADO).exists()
    campos = {"situacao"}
    if not possui_pagamento_ativo:
        ordem.situacao_financeira = SituacaoFinanceira.CANCELADA
        campos.add("situacao_financeira")
    _salvar_ordem(ordem, campos)
    registrar_historico(
        ordem=ordem,
        usuario=usuario,
        acao="ordem_cancelada",
        dados_anteriores=anterior,
        dados_novos={
            **snapshot_ordem(ordem),
            "cancelamento_id": cancelamento.pk,
            "tratamento_financeiro": tratamento_financeiro,
            "motivo": motivo,
        },
    )
    return cancelamento
