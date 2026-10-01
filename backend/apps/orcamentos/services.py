from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.auditoria.services import registrar_historico, snapshot_ordem
from apps.ordens.models import SituacaoOrdem
from apps.ordens.services import _obter_ordem_bloqueada, _salvar_ordem, _mudar_situacao
from apps.usuarios.permissions import exigir_gerente_ou_atendente, exigir_tecnico_da_ordem

from .models import (
    DecisaoOrcamento,
    ItemOrcamento,
    Orcamento,
    SituacaoOrcamento,
    TipoDecisaoOrcamento,
)


def _validar_itens(itens):
    itens = list(itens or [])
    resultado = []
    for indice, dados in enumerate(itens):
        if not isinstance(dados, dict):
            raise ValidationError({"itens": f"O item {indice + 1} precisa ser um objeto."})
        item = ItemOrcamento(
            tipo=dados.get("tipo"),
            descricao=str(dados.get("descricao") or "").strip(),
            quantidade=dados.get("quantidade"),
            valor_unitario=dados.get("valor_unitario"),
        )
        try:
            item.full_clean(exclude=["orcamento"])
        except ValidationError as exc:
            raise ValidationError({"itens": f"Item {indice + 1} inválido: {exc.message_dict}"}) from exc
        resultado.append(item)
    return resultado


@transaction.atomic
def criar_orcamento(*, usuario, ordem, itens=None, observacoes="", valido_ate=None):
    ordem = _obter_ordem_bloqueada(ordem)
    exigir_tecnico_da_ordem(usuario, ordem)
    if ordem.situacao not in {
        SituacaoOrdem.EM_DIAGNOSTICO,
        SituacaoOrdem.AGUARDANDO_APROVACAO,
        SituacaoOrdem.EM_REPARO,
        SituacaoOrdem.AGUARDANDO_PECA,
    }:
        raise ValidationError("Não é possível criar orçamento nesta situação da ordem.")
    if not ordem.diagnostico.strip():
        raise ValidationError("O diagnóstico precisa ser registrado antes do orçamento.")

    itens_validados = _validar_itens(itens)
    ultimo = (
        Orcamento.objects.select_for_update()
        .filter(ordem=ordem)
        .order_by("-versao")
        .first()
    )
    if ultimo and ultimo.situacao == SituacaoOrcamento.RASCUNHO:
        raise ValidationError("Já existe um orçamento em rascunho para esta ordem.")
    versao = ultimo.versao + 1 if ultimo else 1

    orcamento = Orcamento(
        ordem=ordem,
        criador=usuario,
        versao=versao,
        observacoes=str(observacoes or "").strip(),
        valido_ate=valido_ate,
    )
    orcamento.full_clean()
    orcamento.save()
    for item in itens_validados:
        item.orcamento = orcamento
        item.save()

    registrar_historico(
        ordem=ordem,
        usuario=usuario,
        acao="orcamento_criado",
        dados_anteriores=snapshot_ordem(ordem),
        dados_novos={
            **snapshot_ordem(ordem),
            "orcamento_id": orcamento.pk,
            "orcamento_versao": orcamento.versao,
            "itens": [
                {
                    "tipo": item.tipo,
                    "descricao": item.descricao,
                    "quantidade": str(item.quantidade),
                    "valor_unitario": str(item.valor_unitario),
                }
                for item in orcamento.itens.all()
            ],
        },
    )
    return orcamento


@transaction.atomic
def enviar_orcamento(*, usuario, orcamento, valido_ate=None):
    orcamento_id = getattr(orcamento, "pk", orcamento)
    orcamento = (
        Orcamento.objects.select_for_update()
        .select_related("ordem")
        .get(pk=orcamento_id)
    )
    ordem = _obter_ordem_bloqueada(orcamento.ordem)
    exigir_tecnico_da_ordem(usuario, ordem)
    if orcamento.situacao != SituacaoOrcamento.RASCUNHO:
        raise ValidationError("Somente um orçamento em rascunho pode ser enviado.")
    if not ordem.diagnostico.strip():
        raise ValidationError("O diagnóstico precisa ser registrado antes do envio.")
    if not orcamento.itens.exists():
        raise ValidationError("O orçamento precisa ter pelo menos um item para ser enviado.")

    validade = valido_ate or orcamento.valido_ate
    if not validade:
        raise ValidationError({"valido_ate": "Informe a validade do orçamento."})
    if validade < timezone.localdate():
        raise ValidationError({"valido_ate": "A validade não pode estar no passado."})

    anterior_ordem = snapshot_ordem(ordem)
    versoes_substituidas = []
    for anterior in Orcamento.objects.select_for_update().filter(
        ordem=ordem,
        versao__lt=orcamento.versao,
        situacao__in=[SituacaoOrcamento.ENVIADO, SituacaoOrcamento.APROVADO],
    ):
        anterior.situacao = SituacaoOrcamento.SUBSTITUIDO
        anterior.save(update_fields={"situacao"})
        versoes_substituidas.append(anterior.versao)

    orcamento.situacao = SituacaoOrcamento.ENVIADO
    orcamento.enviado_em = timezone.now()
    orcamento.valido_ate = validade
    orcamento.full_clean()
    orcamento.save()

    if ordem.situacao != SituacaoOrdem.AGUARDANDO_APROVACAO:
        _mudar_situacao(ordem, SituacaoOrdem.AGUARDANDO_APROVACAO)
        _salvar_ordem(ordem, {"situacao"})
    registrar_historico(
        ordem=ordem,
        usuario=usuario,
        acao="orcamento_enviado",
        dados_anteriores=anterior_ordem,
        dados_novos={
            **snapshot_ordem(ordem),
            "orcamento_id": orcamento.pk,
            "orcamento_versao": orcamento.versao,
            "valido_ate": validade.isoformat(),
            "versoes_substituidas": versoes_substituidas,
        },
    )
    return orcamento


@transaction.atomic
def registrar_decisao_orcamento(
    *,
    usuario,
    orcamento,
    decisao,
    canal,
    nome_autorizador,
    evidencia=None,
):
    exigir_gerente_ou_atendente(usuario)
    orcamento_id = getattr(orcamento, "pk", orcamento)
    orcamento = (
        Orcamento.objects.select_for_update()
        .select_related("ordem")
        .get(pk=orcamento_id)
    )
    ordem = _obter_ordem_bloqueada(orcamento.ordem)
    if orcamento.situacao != SituacaoOrcamento.ENVIADO:
        raise ValidationError("A decisão só pode ser registrada em orçamento enviado.")
    if orcamento.valido_ate and orcamento.valido_ate < timezone.localdate():
        raise ValidationError("O orçamento expirou; crie e envie uma nova versão.")
    if decisao not in TipoDecisaoOrcamento.values:
        raise ValidationError({"decisao": "Decisão de orçamento inválida."})
    if DecisaoOrcamento.objects.filter(orcamento=orcamento).exists():
        raise ValidationError("Já existe decisão para esta versão do orçamento.")
    if not str(nome_autorizador or "").strip():
        raise ValidationError({"nome_autorizador": "Informe quem autorizou ou recusou."})

    if evidencia is not None:
        from apps.ordens.models import Anexo

        evidencia = evidencia if isinstance(evidencia, Anexo) else Anexo.objects.get(pk=evidencia)

    registro = DecisaoOrcamento(
        orcamento=orcamento,
        registrado_por=usuario,
        decisao=decisao,
        canal=canal,
        nome_autorizador=str(nome_autorizador).strip(),
        evidencia=evidencia,
    )
    registro.full_clean()
    registro.save()

    anterior_ordem = snapshot_ordem(ordem)
    orcamento.situacao = (
        SituacaoOrcamento.APROVADO
        if decisao == TipoDecisaoOrcamento.APROVADO
        else SituacaoOrcamento.RECUSADO
    )
    orcamento.save(update_fields={"situacao"})

    if decisao == TipoDecisaoOrcamento.RECUSADO:
        if ordem.situacao != SituacaoOrdem.PREPARAR_DEVOLUCAO:
            _mudar_situacao(ordem, SituacaoOrdem.PREPARAR_DEVOLUCAO)
            _salvar_ordem(ordem, {"situacao"})
    elif ordem.situacao != SituacaoOrdem.AGUARDANDO_APROVACAO:
        raise ValidationError("A ordem precisa estar aguardando aprovação para iniciar o reparo.")

    registrar_historico(
        ordem=ordem,
        usuario=usuario,
        acao="decisao_orcamento_registrada",
        dados_anteriores=anterior_ordem,
        dados_novos={
            **snapshot_ordem(ordem),
            "orcamento_id": orcamento.pk,
            "orcamento_versao": orcamento.versao,
            "decisao_id": registro.pk,
            "decisao": decisao,
            "canal": canal,
            "nome_autorizador": registro.nome_autorizador,
        },
    )
    return registro
