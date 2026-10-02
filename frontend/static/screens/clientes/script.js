import { bindShell, api, escapeHtml, formatNumber, formatDateTime, handleAuthError, icon, jsonOptions, openModal, state, statusTag, unwrap, showToast, closeModal } from "/static/shared/core.js";

const root = document.querySelector("[data-screen-slot]");
bindShell();

export async function render(options = {}) {
  const term = encodeURIComponent(state.search.clientes || "");
  const filter = state.filters.clientes || "";
  setLoading();
  try {
    const data = unwrap(await api(options.pageUrl || `/clientes/?page=1${term ? `&q=${term}` : ""}${filter ? `&ativo=${filter}` : ""}`));
    state.pages.clientes = { next: data.next || "", previous: data.previous || "" };
    state.cache.clientes = data.results;
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
  empty.innerHTML = '<div class="page-loading"><span class="spinner" role="status" aria-label="Carregando clientes"></span></div>';
}

function renderRows(records, count) {
  const table = root.querySelector("[data-table-wrap]");
  const body = root.querySelector("[data-table-body]");
  const empty = root.querySelector("[data-empty-state]");
  root.querySelector("#search-clientes").value = state.search.clientes || "";
  root.querySelector("[data-client-filter]").value = state.filters.clientes || "";
  if (!records.length) { showEmpty("Nenhum cliente encontrado."); return; }
  body.innerHTML = records.map((item) => `<tr><td class="primary-cell">${escapeHtml(item.nome)}<div class="muted-cell" style="margin-top:4px">${escapeHtml(item.email || "Sem e-mail")}</div></td><td>${escapeHtml(item.telefone)}</td><td class="muted-cell">${escapeHtml(item.documento || "—")}</td><td>${statusTag(item.ativo ? "APROVADO" : "CANCELADA", item.ativo ? "Ativo" : "Inativo")}</td><td class="muted-cell">${formatDateTime(item.criado_em)}</td><td class="right"><button class="icon-button" data-action="client-detail" data-id="${item.id}" aria-label="Ver cliente">${icon("eye")}</button></td></tr>`).join("");
  table.hidden = false; empty.classList.add("hidden");
  updatePagination("clientes", count, records.length);
}

function updatePagination(view, count, loaded) {
  const page = state.pages[view] || {};
  const container = root.querySelector("[data-pagination]");
  if (!count && !page.next && !page.previous) { container.innerHTML = ""; return; }
  container.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 18px;border-top:1px solid var(--border);color:var(--muted);font-size:11px"><span>${formatNumber(loaded)} de ${formatNumber(count)} registros</span><span style="display:flex;gap:6px"><button class="button button-secondary button-sm" data-action="page" data-view="${view}" data-url="${escapeHtml(page.previous || "")}" ${page.previous ? "" : "disabled"}>Anterior</button><button class="button button-secondary button-sm" data-action="page" data-view="${view}" data-url="${escapeHtml(page.next || "")}" ${page.next ? "" : "disabled"}>Próxima</button></span></div>`;
}

function showEmpty(message) {
  const empty = root.querySelector("[data-empty-state]");
  root.querySelector("[data-table-wrap]").hidden = true;
  empty.classList.remove("hidden");
  empty.innerHTML = `<span class="icon-wrap">${icon("info")}</span><p>${escapeHtml(message)}</p><button class="button button-secondary button-sm" data-action="new-client">${icon("plus")}Novo cliente</button>`;
  root.querySelector("[data-pagination]").innerHTML = "";
}

function bind(element) {
  if (element.dataset.bound === "true") return;
  element.dataset.bound = "true";
  element.addEventListener("submit", (event) => {
    if (!event.target.matches("[data-collection-search]")) return;
    event.preventDefault(); state.search.clientes = new FormData(event.target).get("q") || ""; render();
  });
  element.addEventListener("change", (event) => {
    if (event.target.matches("[data-client-filter]")) { state.filters.clientes = event.target.value; render(); }
  });
  element.addEventListener("click", (event) => {
    const action = event.target.closest("[data-action]");
    if (!action) return;
    if (action.dataset.action === "new-client") openCreate();
    if (action.dataset.action === "client-detail") openDetail(action.dataset.id);
    if (action.dataset.action === "refresh-screen") render(); if (action.dataset.action === "page" && action.dataset.url) render({ pageUrl: action.dataset.url });
  });
}

function openCreate() {
  openModal("Novo cliente", "Cadastre os dados principais para abrir ordens com segurança.", `<form id="client-form"><div class="form-grid"><div class="field"><label>Nome <span>*</span></label><input name="nome" required /></div><div class="field"><label>Telefone <span>*</span></label><input name="telefone" required /></div><div class="field"><label>E-mail</label><input name="email" type="email" /></div><div class="field"><label>Documento</label><input name="documento" /></div><div class="field full"><label>Endereço</label><input name="endereco" /></div></div></form>`, `<button class="button button-secondary" data-action="close-modal">Cancelar</button><button class="button button-primary" form="client-form" type="submit">${icon("check")}Salvar</button>`);
  document.getElementById("client-form").addEventListener("submit", async (event) => { event.preventDefault(); try { await api("/clientes/", jsonOptions(Object.fromEntries(new FormData(event.currentTarget).entries()))); closeModal(); showToast("Cliente cadastrado.", "success"); await render(); } catch (error) { if (!handleAuthError(error)) showToast(error.message, "error"); } });
}

function openDetail(id) {
  const item = state.cache.clientes.find((client) => String(client.id) === String(id));
  if (!item) return;
  openModal(item.nome, "Dados do cliente", `<div class="detail-list"><div><div class="detail-item-label">Telefone</div><div class="detail-item-value">${escapeHtml(item.telefone)}</div></div><div><div class="detail-item-label">E-mail</div><div class="detail-item-value">${escapeHtml(item.email || "—")}</div></div><div><div class="detail-item-label">Documento</div><div class="detail-item-value">${escapeHtml(item.documento || "—")}</div></div><div><div class="detail-item-label">Status</div><div class="detail-item-value">${statusTag(item.ativo ? "APROVADO" : "CANCELADA", item.ativo ? "Ativo" : "Inativo")}</div></div><div class="full"><div class="detail-item-label">Endereço</div><div class="detail-item-value">${escapeHtml(item.endereco || "—")}</div></div></div>`, '<button class="button button-secondary" data-action="close-modal">Fechar</button>');
}

render();











