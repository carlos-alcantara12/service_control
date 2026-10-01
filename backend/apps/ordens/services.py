from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.auditoria.services import registrar_historico, snapshot_ordem
from apps.clientes.models import Cliente
from apps.equipamentos.models import Equipamento
from apps.usuarios.models import PerfilUsuario, Usuario
from apps.usuarios.permissions import (
    exigir_gerente,
    exigir_gerente_ou_atendente,
    exigir_tecnico_da_ordem,
    exigir_usuario_ativo,
)

from .models import (
    Anexo,
    AtividadeServico,
    Entrega,
    OrdemServico,
    PecaUtilizada,
    PrioridadeOrdem,
    SituacaoOrdem,
    TipoAtividade,
)


TRANSICOES_PERMITIDAS = {
    SituacaoOrdem.RECEBIDA: {
        SituacaoOrdem.EM_DIAGNOSTICO,
        SituacaoOrdem.CANCELADA,
    },
    SituacaoOrdem.EM_DIAGNOSTICO: {
        SituacaoOrdem.AGUARDANDO_APROVACAO,
        SituacaoOrdem.CANCELADA,
    },
    SituacaoOrdem.AGUARDANDO_APROVACAO: {
        SituacaoOrdem.EM_REPARO,
        SituacaoOrdem.PREPARAR_DEVOLUCAO,
        SituacaoOrdem.CANCELADA,
    },
    SituacaoOrdem.EM_REPARO: {
        SituacaoOrdem.AGUARDANDO_PECA,
        SituacaoOrdem.EM_TESTES,
        SituacaoOrdem.PRONTA_ENTREGA,
        SituacaoOrdem.AGUARDANDO_APROVACAO,
        SituacaoOrdem.CANCELADA,
    },
    SituacaoOrdem.AGUARDANDO_PECA: {
        SituacaoOrdem.EM_REPARO,
        SituacaoOrdem.CANCELADA,
    },
    SituacaoOrdem.EM_TESTES: {
        SituacaoOrdem.EM_REPARO,
        SituacaoOrdem.PRONTA_ENTREGA,
        SituacaoOrdem.CANCELADA,
    },
    SituacaoOrdem.PREPARAR_DEVOLUCAO: {
        SituacaoOrdem.PRONTA_ENTREGA,
        SituacaoOrdem.CANCELADA,
    },
    SituacaoOrdem.PRONTA_ENTREGA: {
        SituacaoOrdem.ENTREGUE,
        SituacaoOrdem.CANCELADA,
    },
    SituacaoOrdem.ENTREGUE: set(),
    SituacaoOrdem.CANCELADA: set(),
}


def _resolve(model, value):
    if isinstance(value, model):
        return value
    return model.objects.get(pk=value)


def _obter_ordem_bloqueada(ordem):
    ordem_id = getattr(ordem, "pk", ordem)
    return (
        OrdemServico.objects.select_for_update()
        .select_related("cliente", "equipamento", "tecnico", "ordem_original")
        .get(pk=ordem_id)
    )


def _salvar_ordem(ordem, campos):
    ordem.full_clean()
    ordem.save(update_fields=set(campos))


def _mudar_situacao(ordem, nova_situacao):
    if ordem.situacao == nova_situacao:
        return
    permitidas = TRANSICOES_PERMITIDAS.get(ordem.situacao, set())
    if nova_situacao not in permitidas:
        nova_display = dict(SituacaoOrdem.choices).get(nova_situacao, nova_situacao)
        raise ValidationError(
            f"Transição inválida: {ordem.get_situacao_display()} → "
            f"{nova_display}."
        )
    ordem.situacao = nova_situacao


def _decimal(value, field_name, *, maior_que_zero=False, nao_negativo=False):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError({field_name: "Informe um valor monetário válido."}) from exc
    if maior_que_zero and result <= 0:
        raise ValidationError({field_name: "O valor precisa ser maior que zero."})
    if nao_negativo and result < 0:
        raise ValidationError({field_name: "O valor não pode ser negativo."})
    return result


@transaction.atomic
def abrir_ordem(
    *,
    atendente,
    cliente,
    equipamento,
    defeito_relatado,
    condicoes_entrada,
    acessorios="",
    prioridade=PrioridadeOrdem.NORMAL,
    previsao_entrega=None,
):
    """Abre uma OS e grava a criação e os dados de recebimento no histórico."""
    exigir_gerente_ou_atendente(atendente)
    cliente = _resolve(Cliente, cliente)
    equipamento = _resolve(Equipamento, equipamento)
    if equipamento.cliente_id != cliente.pk:
        raise ValidationError({"equipamento": "O equipamento não pertence ao cliente informado."})
    if not str(defeito_relatado or "").strip():
        raise ValidationError({"defeito_relatado": "O defeito relatado é obrigatório."})
    if not str(condicoes_entrada or "").strip():
        raise ValidationError({"condicoes_entrada": "As condições de entrada são obrigatórias."})

    ordem = OrdemServico(
        cliente=cliente,
        equipamento=equipamento,
        atendente=atendente,
        defeito_relatado=str(defeito_relatado).strip(),
        condicoes_entrada=str(condicoes_entrada).strip(),
        acessorios=str(acessorios or "").strip(),
        prioridade=prioridade,
        previsao_entrega=previsao_entrega,
    )
    ordem.full_clean()
    ordem.save()
    registrar_historico(
        ordem=ordem,
        usuario=atendente,
        acao="ordem_aberta",
        dados_novos=snapshot_ordem(ordem),
    )
    return ordem


@transaction.atomic
def atribuir_tecnico(*, usuario, ordem, tecnico):
    exigir_gerente(usuario)
    tecnico = _resolve(Usuario, tecnico)
    if tecnico.perfil != PerfilUsuario.TECNICO:
        raise ValidationError({"tecnico": "O responsável precisa ter perfil de técnico."})
    if not tecnico.ativo:
        raise ValidationError({"tecnico": "O técnico responsável precisa estar ativo."})

    ordem = _obter_ordem_bloqueada(ordem)
    if ordem.situacao in {SituacaoOrdem.ENTREGUE, SituacaoOrdem.CANCELADA}:
        raise ValidationError("Não é possível atribuir técnico a uma ordem encerrada.")
    if ordem.tecnico_id == tecnico.pk:
        return ordem
    anterior = snapshot_ordem(ordem)
    ordem.tecnico = tecnico
    _salvar_ordem(ordem, {"tecnico"})
    registrar_historico(
        ordem=ordem,
        usuario=usuario,
        acao="tecnico_atribuido",
        dados_anteriores=anterior,
        dados_novos=snapshot_ordem(ordem),
    )
    return ordem


@transaction.atomic
def registrar_diagnostico(*, usuario, ordem, diagnostico):
    ordem = _obter_ordem_bloqueada(ordem)
    exigir_tecnico_da_ordem(usuario, ordem)
    if not ordem.tecnico_id or not ordem.tecnico.ativo:
        raise ValidationError("A ordem precisa ter um técnico ativo atribuído.")
    diagnostico = str(diagnostico or "").strip()
    if not diagnostico:
        raise ValidationError({"diagnostico": "O diagnóstico é obrigatório."})
    if ordem.situacao not in {SituacaoOrdem.RECEBIDA, SituacaoOrdem.EM_DIAGNOSTICO}:
        raise ValidationError("O diagnóstico não pode ser alterado nesta situação.")

    anterior = snapshot_ordem(ordem)
    ordem.diagnostico = diagnostico
    _mudar_situacao(ordem, SituacaoOrdem.EM_DIAGNOSTICO)
    _salvar_ordem(ordem, {"diagnostico", "situacao"})
    registrar_historico(
        ordem=ordem,
        usuario=usuario,
        acao="diagnostico_registrado",
        dados_anteriores=anterior,
        dados_novos=snapshot_ordem(ordem),
    )
    return ordem


@transaction.atomic
def registrar_atividade(*, usuario, ordem, tipo, descricao, resultado=""):
    ordem = _obter_ordem_bloqueada(ordem)
    exigir_tecnico_da_ordem(usuario, ordem)
    if ordem.situacao not in {
        SituacaoOrdem.EM_DIAGNOSTICO,
        SituacaoOrdem.EM_REPARO,
        SituacaoOrdem.AGUARDANDO_PECA,
        SituacaoOrdem.EM_TESTES,
    }:
        raise ValidationError("A atividade não pode ser registrada nesta situação da ordem.")
    if not ordem.tecnico_id:
        raise ValidationError("A ordem precisa ter técnico atribuído.")
    descricao = str(descricao or "").strip()
    resultado = str(resultado or "").strip()
    if not descricao:
        raise ValidationError({"descricao": "A descrição da atividade é obrigatória."})

    atividade = AtividadeServico(
        ordem=ordem,
        tecnico=ordem.tecnico,
        tipo=tipo,
        descricao=descricao,
        resultado=resultado,
    )
    atividade.full_clean()
    atividade.save()
    registrar_historico(
        ordem=ordem,
        usuario=usuario,
        acao="atividade_registrada",
        dados_novos={
            "atividade_id": atividade.pk,
            "tipo": atividade.tipo,
            "descricao": atividade.descricao,
            "resultado": atividade.resultado,
        },
    )
    return atividade


@transaction.atomic
def iniciar_reparo(*, usuario, ordem):
    from apps.orcamentos.models import DecisaoOrcamento, Orcamento, TipoDecisaoOrcamento

    ordem = _obter_ordem_bloqueada(ordem)
    exigir_tecnico_da_ordem(usuario, ordem)
    if ordem.situacao != SituacaoOrdem.AGUARDANDO_APROVACAO:
        raise ValidationError("O reparo só pode iniciar aguardando aprovação.")

    hoje = timezone.localdate()
    orcamento = (
        Orcamento.objects.select_for_update()
        .filter(
            ordem=ordem,
            situacao="APROVADO",
            valido_ate__gte=hoje,
            decisao__decisao=TipoDecisaoOrcamento.APROVADO,
        )
        .order_by("-versao")
        .first()
    )
    if not orcamento:
        raise ValidationError("Não existe aprovação válida para iniciar o reparo.")
    if not DecisaoOrcamento.objects.filter(
        orcamento=orcamento,
        decisao=TipoDecisaoOrcamento.APROVADO,
    ).exists():
        raise ValidationError("A aprovação do orçamento não foi encontrada.")

    anterior = snapshot_ordem(ordem)
    _mudar_situacao(ordem, SituacaoOrdem.EM_REPARO)
    _salvar_ordem(ordem, {"situacao"})
    registrar_historico(
        ordem=ordem,
        usuario=usuario,
        acao="reparo_iniciado",
        dados_anteriores=anterior,
        dados_novos={
            **snapshot_ordem(ordem),
            "orcamento_id": orcamento.pk,
            "orcamento_versao": orcamento.versao,
        },
    )
    return ordem


@transaction.atomic
def registrar_peca_utilizada(
    *,
    usuario,
    ordem,
    descricao,
    quantidade,
    custo_unitario,
):
    ordem = _obter_ordem_bloqueada(ordem)
    exigir_tecnico_da_ordem(usuario, ordem)
    if ordem.situacao != SituacaoOrdem.EM_REPARO:
        raise ValidationError("Peças só podem ser utilizadas durante o reparo.")
    descricao = str(descricao or "").strip()
    if not descricao:
        raise ValidationError({"descricao": "A descrição da peça é obrigatória."})
    quantidade = _decimal(quantidade, "quantidade", maior_que_zero=True)
    custo_unitario = _decimal(custo_unitario, "custo_unitario", nao_negativo=True)

    peca = PecaUtilizada(
        ordem=ordem,
        registrado_por=usuario,
        descricao=descricao,
        quantidade=quantidade,
        custo_unitario=custo_unitario,
    )
    peca.full_clean()
    peca.save()
    registrar_historico(
        ordem=ordem,
        usuario=usuario,
        acao="peca_utilizada_registrada",
        dados_novos={
            "peca_id": peca.pk,
            "descricao": peca.descricao,
            "quantidade": str(peca.quantidade),
            "custo_unitario": str(peca.custo_unitario),
        },
    )
    return peca


@transaction.atomic
def alterar_prazo(*, usuario, ordem, previsao_entrega, justificativa):
    exigir_gerente(usuario)
    ordem = _obter_ordem_bloqueada(ordem)
    if ordem.situacao in {SituacaoOrdem.ENTREGUE, SituacaoOrdem.CANCELADA}:
        raise ValidationError("Não é possível alterar o prazo de uma ordem encerrada.")
    justificativa = str(justificativa or "").strip()
    if not justificativa:
        raise ValidationError({"justificativa": "A alteração de prazo exige justificativa."})
    if previsao_entrega is None:
        raise ValidationError({"previsao_entrega": "Informe o novo prazo."})
    if ordem.previsao_entrega == previsao_entrega:
        raise ValidationError("O novo prazo precisa ser diferente do prazo atual.")

    anterior = snapshot_ordem(ordem)
    ordem.previsao_entrega = previsao_entrega
    _salvar_ordem(ordem, {"previsao_entrega"})
    registrar_historico(
        ordem=ordem,
        usuario=usuario,
        acao="prazo_alterado",
        dados_anteriores=anterior,
        dados_novos=snapshot_ordem(ordem),
        justificativa=justificativa,
    )
    return ordem


@transaction.atomic
def concluir_testes(*, usuario, ordem, resultado, aprovado):
    ordem = _obter_ordem_bloqueada(ordem)
    exigir_tecnico_da_ordem(usuario, ordem)
    if ordem.situacao not in {SituacaoOrdem.EM_REPARO, SituacaoOrdem.EM_TESTES}:
        raise ValidationError("A ordem não está pronta para testes.")
    resultado = str(resultado or "").strip()
    if not resultado:
        raise ValidationError({"resultado": "O resultado dos testes é obrigatório."})
    if not isinstance(aprovado, bool):
        raise ValidationError({"aprovado": "Informe se os testes foram aprovados."})

    atividade = AtividadeServico(
        ordem=ordem,
        tecnico=ordem.tecnico,
        tipo=TipoAtividade.TESTE,
        descricao="Testes finais do equipamento",
        resultado=resultado,
    )
    atividade.full_clean()
    atividade.save()

    anterior = snapshot_ordem(ordem)
    if aprovado:
        _mudar_situacao(ordem, SituacaoOrdem.PRONTA_ENTREGA)
        ordem.conclusao_em = timezone.now()
    else:
        _mudar_situacao(ordem, SituacaoOrdem.EM_REPARO)
        ordem.conclusao_em = None
    _salvar_ordem(ordem, {"situacao", "conclusao_em"})
    registrar_historico(
        ordem=ordem,
        usuario=usuario,
        acao="testes_concluidos",
        dados_anteriores=anterior,
        dados_novos={
            **snapshot_ordem(ordem),
            "atividade_id": atividade.pk,
            "aprovado": aprovado,
            "resultado": resultado,
        },
    )
    return ordem


@transaction.atomic
def registrar_entrega(
    *,
    usuario,
    ordem,
    recebedor,
    identificacao="",
    comprovante=None,
    observacoes="",
    autorizacao_excecao_por=None,
):
    exigir_gerente_ou_atendente(usuario)
    ordem = _obter_ordem_bloqueada(ordem)
    if ordem.situacao not in {
        SituacaoOrdem.PRONTA_ENTREGA,
        SituacaoOrdem.PREPARAR_DEVOLUCAO,
    }:
        raise ValidationError("A ordem não está pronta para entrega.")
    if Entrega.objects.filter(ordem=ordem).exists():
        raise ValidationError("A entrega desta ordem já foi registrada.")
    recebedor = str(recebedor or "").strip()
    if not recebedor:
        raise ValidationError({"recebedor": "Informe quem recebeu o equipamento."})

    autorizador = None
    if autorizacao_excecao_por is not None:
        autorizador = _resolve(Usuario, autorizacao_excecao_por)
        exigir_gerente(autorizador)
        if ordem.saldo_pendente <= 0:
            raise ValidationError("Não é necessário autorizar exceção sem saldo pendente.")
    elif ordem.saldo_pendente > 0:
        raise ValidationError(
            "A entrega exige quitação ou autorização de exceção por um gerente."
        )

    comprovante = _resolve(Anexo, comprovante) if comprovante is not None else None
    entrega = Entrega(
        ordem=ordem,
        funcionario=usuario,
        recebedor=recebedor,
        identificacao=str(identificacao or "").strip(),
        comprovante=comprovante,
        observacoes=str(observacoes or "").strip(),
        autorizacao_excecao_por=autorizador,
    )
    entrega.full_clean()
    entrega.save()

    anterior = snapshot_ordem(ordem)
    _mudar_situacao(ordem, SituacaoOrdem.ENTREGUE)
    _salvar_ordem(ordem, {"situacao"})
    registrar_historico(
        ordem=ordem,
        usuario=usuario,
        acao="entrega_registrada",
        dados_anteriores=anterior,
        dados_novos={
            **snapshot_ordem(ordem),
            "entrega_id": entrega.pk,
            "recebedor": entrega.recebedor,
            "autorizacao_excecao_por_id": getattr(autorizador, "pk", None),
        },
    )
    return entrega


@transaction.atomic
def abrir_retorno(
    *,
    usuario,
    ordem_original,
    defeito_relatado,
    condicoes_entrada,
    acessorios="",
    prioridade=PrioridadeOrdem.NORMAL,
    previsao_entrega=None,
):
    exigir_gerente_ou_atendente(usuario)
    ordem_original = _obter_ordem_bloqueada(ordem_original)
    if ordem_original.situacao != SituacaoOrdem.ENTREGUE:
        raise ValidationError("Só é possível abrir retorno de uma ordem entregue.")
    defeito_relatado = str(defeito_relatado or "").strip()
    condicoes_entrada = str(condicoes_entrada or "").strip()
    if not defeito_relatado or not condicoes_entrada:
        raise ValidationError("Defeito e condições de entrada são obrigatórios.")

    retorno = OrdemServico(
        cliente=ordem_original.cliente,
        equipamento=ordem_original.equipamento,
        atendente=usuario,
        ordem_original=ordem_original,
        defeito_relatado=defeito_relatado,
        condicoes_entrada=condicoes_entrada,
        acessorios=str(acessorios or "").strip(),
        prioridade=prioridade,
        previsao_entrega=previsao_entrega,
    )
    retorno.full_clean()
    retorno.save()
    registrar_historico(
        ordem=retorno,
        usuario=usuario,
        acao="retorno_aberto",
        dados_novos={
            **snapshot_ordem(retorno),
            "ordem_original_id": ordem_original.pk,
        },
    )
    registrar_historico(
        ordem=ordem_original,
        usuario=usuario,
        acao="retorno_vinculado",
        dados_novos={
            "ordem_retorno_id": retorno.pk,
            "ordem_retorno_numero": retorno.numero,
        },
    )
    return retorno
