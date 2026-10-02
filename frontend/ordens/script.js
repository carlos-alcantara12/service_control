import { bindShell, api, escapeHtml, formatDateTime, formatDate, formatMoney, formatNumber, emptyMarkup, handleAuthError, icon, jsonOptions, labelize, loadingMarkup, openModal, closeModal, state, statusTag, unwrap, showToast } from "../shared/core.js";

const root = document.querySelector("[data-screen-slot]");
bindShell();

export async function render(options = {}) {
  const term = encodeURIComponent(state.search.ordens || "");
  const filter = state.filters.ordens || "";
  setLoading();
  const path = options.pageUrl || `/ordens/?page=1${term ? `&q=${term}` : ""}${filter ? `&situacao=${encodeURIComponent(filter)}` : ""}`;
  try {
    const data = unwrap(await api(path));
    state.pages.ordens = { next: data.next || "", previous: data.previous || "" };
    state.cache.ordens = data.results;
    renderRows(data.results, data.count);
  } catch (error) {
    if (handleAuthError(error)) return;
    showEmpty(error.message);
  }
  bind(root);
}

function setLoading() {
  root.querySelector("[data-table-wrap]").hidden = true;
  const empty = root.querySelector("[data-empty-state]");
  empty.classList.remove("hidden");
  empty.innerHTML = '<div class="page-loading"><span class="spinner" role="status" aria-label="Carregando ordens"></span></div>';
}

function renderRows(records, count) {
  const table=root.querySelector("[data-table-wrap]"), body=root.querySelector("[data-table-body]"), empty=root.querySelector("[data-empty-state]");
  root.querySelector("#search-ordens").value=state.search.ordens||"";
  root.querySelector("[data-order-filter]").value=state.filters.ordens||"";
  if(!records.length){showEmpty("Nenhuma ordem de serviço encontrada.");return;}
  body.innerHTML=records.map((item)=>`<tr><td class="primary-cell"><button class="button-ghost row-action" data-action="order-detail" data-id="${item.id}">${escapeHtml(item.numero)}</button><div class="muted-cell" style="margin-top:4px">${escapeHtml(item.equipamento_descricao)}</div></td><td>${escapeHtml(item.cliente_nome)}</td><td class="muted-cell">${escapeHtml(item.tecnico_nome||item.atendente_nome||"Não atribuído")}</td><td>${statusTag(item.situacao,item.situacao_display)}</td><td>${statusTag(item.prioridade,item.prioridade_display)}</td><td class="muted-cell">${formatDateTime(item.entrada_em)}</td><td class="right"><button class="icon-button" data-action="order-detail" data-id="${item.id}" aria-label="Abrir ordem">${icon("chevronRight")}</button></td></tr>`).join("");
  table.hidden=false;empty.classList.add("hidden");updatePagination("ordens", count, records.length);
}

function updatePagination(view, count, loaded) {
  const page = state.pages[view] || {};
  const container = root.querySelector("[data-pagination]");
  if (!count && !page.next && !page.previous) { container.innerHTML = ""; return; }
  container.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 18px;border-top:1px solid var(--border);color:var(--muted);font-size:11px"><span>${formatNumber(loaded)} de ${formatNumber(count)} registros</span><span style="display:flex;gap:6px"><button class="button button-secondary button-sm" data-action="page" data-view="${view}" data-url="${escapeHtml(page.previous || "")}" ${page.previous ? "" : "disabled"}>Anterior</button><button class="button button-secondary button-sm" data-action="page" data-view="${view}" data-url="${escapeHtml(page.next || "")}" ${page.next ? "" : "disabled"}>Próxima</button></span></div>`;
}

function showEmpty(message){const empty=root.querySelector("[data-empty-state]");root.querySelector("[data-table-wrap]").hidden=true;empty.classList.remove("hidden");empty.innerHTML=`<span class="icon-wrap">${icon("info")}</span><p>${escapeHtml(message)}</p><button class="button button-secondary button-sm" data-action="new-order">${icon("plus")}Nova ordem</button>`;root.querySelector("[data-pagination]").innerHTML="";}

function bind(element){
  if(element.dataset.bound==="true")return;
  element.dataset.bound="true";
  element.addEventListener("submit",(event)=>{if(!event.target.matches("[data-collection-search]"))return;event.preventDefault();state.search.ordens=new FormData(event.target).get("q")||"";render();});
  element.addEventListener("change",(event)=>{if(event.target.matches("[data-order-filter]")){state.filters.ordens=event.target.value;render();}});
  element.addEventListener("click",(event)=>{const action=event.target.closest("[data-action]");if(!action)return;if(action.dataset.action==="new-order")return openCreateModal("ordem");if(action.dataset.action==="order-detail")return openOrderDetail(action.dataset.id);if(action.dataset.action==="refresh-screen")render();if(action.dataset.action==="page"&&action.dataset.url)render({pageUrl:action.dataset.url});});
}

export async function openCreateModal(type) {
  if (type === "cliente") return openSimpleCreate("cliente", "Novo cliente", "Cadastre os dados principais para abrir ordens com segurança.", `<div class="form-grid"><div class="field"><label>Nome <span>*</span></label><input name="nome" required /></div><div class="field"><label>Telefone <span>*</span></label><input name="telefone" required /></div><div class="field"><label>E-mail</label><input name="email" type="email" /></div><div class="field"><label>Documento</label><input name="documento" /></div><div class="field full"><label>Endereço</label><input name="endereco" /></div></div>`);
  if (type === "usuario") return openSimpleCreate("usuario", "Novo usuário", "Defina o perfil e o acesso inicial da pessoa na operação.", `<div class="form-grid"><div class="field"><label>Nome <span>*</span></label><input name="nome" required /></div><div class="field"><label>Login <span>*</span></label><input name="login" required /></div><div class="field"><label>E-mail</label><input name="email" type="email" /></div><div class="field"><label>Perfil <span>*</span></label><select name="perfil" required><option value="ATENDENTE">Atendente</option><option value="TECNICO">Técnico</option><option value="GERENTE">Gerente</option></select></div><div class="field full"><label>Senha inicial <span>*</span></label><input name="password" type="password" minlength="8" required /></div></div>`);
  if (!state.cache.clientes.length) state.cache.clientes = unwrap(await api("/clientes/?ativo=1")).results;
  if (type === "equipamento") return openSimpleCreate("equipamento", "Novo equipamento", "Vincule o equipamento ao cliente correto para manter o histórico completo.", `<div class="form-grid"><div class="field full"><label>Cliente <span>*</span></label><select name="cliente" required>${state.cache.clientes.map((item) => `<option value="${item.id}">${escapeHtml(item.nome)}</option>`).join("")}</select></div><div class="field"><label>Categoria <span>*</span></label><input name="categoria" required /></div><div class="field"><label>Marca <span>*</span></label><input name="marca" required /></div><div class="field"><label>Modelo <span>*</span></label><input name="modelo" required /></div><div class="field"><label>Número de série</label><input name="numero_serie" /></div></div>`);
  if (!state.cache.equipamentos.length) state.cache.equipamentos = unwrap(await api("/equipamentos/?page=1")).results;
  return openSimpleCreate("ordem", "Nova ordem de serviço", "Abra um atendimento com os dados mínimos para iniciar o fluxo.", `<div class="form-grid"><div class="field"><label>Cliente <span>*</span></label><select name="cliente" required>${state.cache.clientes.map((item) => `<option value="${item.id}">${escapeHtml(item.nome)}</option>`).join("")}</select></div><div class="field"><label>Equipamento <span>*</span></label><select name="equipamento" required>${state.cache.equipamentos.map((item) => `<option value="${item.id}">${escapeHtml(item.categoria)} · ${escapeHtml(item.marca)} ${escapeHtml(item.modelo)}</option>`).join("")}</select></div><div class="field"><label>Prioridade</label><select name="prioridade"><option value="NORMAL">Normal</option><option value="BAIXA">Baixa</option><option value="ALTA">Alta</option><option value="URGENTE">Urgente</option></select></div><div class="field"><label>Previsão de entrega</label><input name="previsao_entrega" type="date" /></div><div class="field full"><label>Defeito relatado <span>*</span></label><textarea name="defeito_relatado" required></textarea></div><div class="field full"><label>Condições de entrada <span>*</span></label><textarea name="condicoes_entrada" required></textarea></div><div class="field full"><label>Acessórios</label><input name="acessorios" /></div></div>`);
}

function openSimpleCreate(type, title, description, body) {
  openModal(title, description, `<form id="entity-form" data-entity="${type}">${body}</form>`, `<button class="button button-secondary" type="button" data-action="close-modal">Cancelar</button><button class="button button-primary" form="entity-form" type="submit">${icon("check")}Salvar</button>`);
  document.getElementById("entity-form").addEventListener("submit", submitEntity);
}

async function submitEntity(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const entity = form.dataset.entity;
  const data = Object.fromEntries(new FormData(form).entries());
  try {
    if (entity === "ordem" && !data.previsao_entrega) delete data.previsao_entrega;
    const endpoint = entity === "ordem" ? "/ordens/" : entity === "usuario" ? "/usuarios/" : `/${entity}s/`;
    await api(endpoint, jsonOptions(data));
    closeModal(); showToast("Registro salvo com sucesso.", "success"); await render();
  } catch (error) { if (!handleAuthError(error)) showToast(error.message, "error"); }
}

export async function openOrderDetail(id) {
  openModal("Carregando ordem", "Consultando o histórico do atendimento.", loadingMarkup());
  try {
    const order = await api(`/ordens/${id}/`);
    const budgets = (order.orcamentos || []).map((item) => `<tr><td>Versão ${escapeHtml(item.versao)}</td><td>${statusTag(item.situacao, item.situacao_display)}</td><td class="right">${formatMoney(item.total)}</td></tr>`).join("");
    const payments = (order.pagamentos || []).map((item) => `<tr><td>${escapeHtml(item.identificador_operacao)}</td><td>${statusTag(item.situacao, item.situacao_display)}</td><td class="right">${formatMoney(item.valor)}</td></tr>`).join("");
    const body = `<div class="detail-grid"><div><div class="detail-list"><div><div class="detail-item-label">Cliente</div><div class="detail-item-value">${escapeHtml(order.cliente_nome)}</div></div><div><div class="detail-item-label">Equipamento</div><div class="detail-item-value">${escapeHtml(order.equipamento_descricao)}</div></div><div><div class="detail-item-label">Situação</div><div class="detail-item-value">${statusTag(order.situacao, order.situacao_display)}</div></div><div><div class="detail-item-label">Financeiro</div><div class="detail-item-value">${statusTag(order.situacao_financeira, order.situacao_financeira_display)}</div></div><div><div class="detail-item-label">Entrada</div><div class="detail-item-value">${formatDateTime(order.entrada_em)}</div></div><div><div class="detail-item-label">Previsão</div><div class="detail-item-value">${formatDate(order.previsao_entrega)}</div></div></div><div class="panel" style="margin-top:20px"><div class="panel-header"><div><h3 class="panel-title">Orçamentos</h3></div></div>${budgets ? `<div class="table-wrap"><table class="data-table"><thead><tr><th>Versão</th><th>Situação</th><th class="right">Total</th></tr></thead><tbody>${budgets}</tbody></table></div>` : emptyMarkup("Nenhum orçamento registrado.")}</div><div class="panel" style="margin-top:18px"><div class="panel-header"><div><h3 class="panel-title">Pagamentos</h3></div></div>${payments ? `<div class="table-wrap"><table class="data-table"><thead><tr><th>Operação</th><th>Status</th><th class="right">Valor</th></tr></thead><tbody>${payments}</tbody></table></div>` : emptyMarkup("Nenhum pagamento registrado.")}</div></div><div class="panel"><div class="panel-header"><div><h3 class="panel-title">Atendimento</h3><p class="panel-subtitle">${escapeHtml(order.defeito_relatado || "Sem descrição")}</p></div></div><div class="panel-body"><div class="timeline-item"><span class="timeline-dot"></span><div><div class="timeline-label">${escapeHtml(labelize(order.situacao))}</div><div class="timeline-meta">Entrada registrada em ${formatDateTime(order.entrada_em)}</div></div></div></div></div></div>`;
    openModal(order.numero || `Ordem #${order.id}`, `${order.cliente_nome || ""} · ${labelize(order.situacao)}`, body, `<button class="button button-secondary" type="button" data-action="close-modal">Fechar</button><button class="button button-secondary" type="button" data-order-action="orcamento" data-order-id="${order.id}">${icon("fileText")}Novo orçamento</button><button class="button button-primary" type="button" data-order-action="pagamento" data-order-id="${order.id}">${icon("dollar")}Registrar pagamento</button>`, true);
    document.getElementById("modal-backdrop").addEventListener("click", (event) => { const button = event.target.closest("[data-order-action]"); if (button) openOrderAction(button.dataset.orderAction, button.dataset.orderId); });
  } catch (error) { closeModal(); if (!handleAuthError(error)) showToast(error.message, "error"); }
}

function openOrderAction(type, orderId) {
  if (type === "pagamento") openModal("Registrar pagamento", "Associe o recebimento a esta ordem para atualizar o saldo.", `<form id="entity-form" data-entity="pagamento" data-order-id="${orderId}"><div class="form-grid"><div class="field"><label>Valor <span>*</span></label><input name="valor" type="number" min="0.01" step="0.01" required /></div><div class="field"><label>Forma <span>*</span></label><select name="forma"><option value="PIX">PIX</option><option value="DINHEIRO">Dinheiro</option><option value="CARTAO_CREDITO">Cartão de crédito</option><option value="CARTAO_DEBITO">Cartão de débito</option><option value="TRANSFERENCIA">Transferência</option><option value="OUTRO">Outro</option></select></div><div class="field"><label>Identificador da operação <span>*</span></label><input name="identificador_operacao" required /></div><div class="field"><label>Referência</label><input name="referencia" /></div></div></form>`, `<button class="button button-secondary" type="button" data-action="close-modal">Cancelar</button><button class="button button-primary" form="entity-form" type="submit">${icon("check")}Confirmar pagamento</button>`);
  else openModal("Novo orçamento", "Crie uma versão vinculada à ordem selecionada.", `<form id="entity-form" data-entity="orcamento" data-order-id="${orderId}"><div class="form-grid"><div class="field full"><label>Descrição do item <span>*</span></label><input name="descricao" required /></div><div class="field"><label>Quantidade <span>*</span></label><input name="quantidade" type="number" min="0.001" step="0.001" value="1" required /></div><div class="field"><label>Valor unitário <span>*</span></label><input name="valor_unitario" type="number" min="0" step="0.01" required /></div><div class="field"><label>Válido até</label><input name="valido_ate" type="date" /></div><div class="field full"><label>Observações</label><textarea name="observacoes"></textarea></div></div></form>`, `<button class="button button-secondary" type="button" data-action="close-modal">Cancelar</button><button class="button button-primary" form="entity-form" type="submit">${icon("check")}Criar orçamento</button>`);
  document.getElementById("entity-form").addEventListener("submit", submitAction);
}

async function submitAction(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  try {
    if (form.dataset.entity === "pagamento") await api(`/ordens/${form.dataset.orderId}/pagamentos/`, jsonOptions(data));
    else await api(`/ordens/${form.dataset.orderId}/orcamentos/`, jsonOptions({ valido_ate: data.valido_ate || null, observacoes: data.observacoes || "", itens: [{ tipo: "SERVICO", descricao: data.descricao, quantidade: data.quantidade, valor_unitario: data.valor_unitario }] }));
    closeModal(); showToast("Operação registrada com sucesso.", "success"); await render();
  } catch (error) { if (!handleAuthError(error)) showToast(error.message, "error"); }
}
render();




