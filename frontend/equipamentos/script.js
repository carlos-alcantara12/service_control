import { bindShell, api, escapeHtml, formatNumber, formatDateTime, handleAuthError, icon, jsonOptions, openModal, state, unwrap, showToast, closeModal } from "../shared/core.js";

const root = document.querySelector("[data-screen-slot]");
bindShell();

export async function render(options = {}) {
  const term = encodeURIComponent(state.search.equipamentos || "");
  setLoading();
  try {
    const data = unwrap(await api(options.pageUrl || `/equipamentos/?page=1${term ? `&q=${term}` : ""}`));
    state.pages.equipamentos = { next: data.next || "", previous: data.previous || "" };
    state.cache.equipamentos = data.results;
    renderRows(data.results, data.count);
  } catch (error) { if (handleAuthError(error)) return; showEmpty(error.message); }
  bind(root);
}

function setLoading() {
  root.querySelector("[data-table-wrap]").hidden = true;
  const empty = root.querySelector("[data-empty-state]");
  empty.classList.remove("hidden");
  empty.innerHTML = '<div class="page-loading"><span class="spinner" role="status" aria-label="Carregando equipamentos"></span></div>';
}

function renderRows(records, count) {
  const table = root.querySelector("[data-table-wrap]"), body = root.querySelector("[data-table-body]"), empty = root.querySelector("[data-empty-state]");
  root.querySelector("#search-equipamentos").value = state.search.equipamentos || "";
  if (!records.length) { showEmpty("Nenhum equipamento encontrado."); return; }
  body.innerHTML = records.map((item) => `<tr><td class="primary-cell">${escapeHtml(item.categoria)} · ${escapeHtml(item.marca)} ${escapeHtml(item.modelo)}</td><td>${escapeHtml(item.cliente_nome)}</td><td class="muted-cell">${escapeHtml(item.numero_serie || "—")}</td><td class="muted-cell">${formatDateTime(item.criado_em)}</td><td class="right"><button class="icon-button" data-action="equipment-detail" data-id="${item.id}" aria-label="Ver equipamento">${icon("eye")}</button></td></tr>`).join("");
  table.hidden = false; empty.classList.add("hidden"); updatePagination("equipamentos", count, records.length);
}

function updatePagination(view, count, loaded) {
  const page = state.pages[view] || {};
  const container = root.querySelector("[data-pagination]");
  if (!count && !page.next && !page.previous) { container.innerHTML = ""; return; }
  container.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 18px;border-top:1px solid var(--border);color:var(--muted);font-size:11px"><span>${formatNumber(loaded)} de ${formatNumber(count)} registros</span><span style="display:flex;gap:6px"><button class="button button-secondary button-sm" data-action="page" data-view="${view}" data-url="${escapeHtml(page.previous || "")}" ${page.previous ? "" : "disabled"}>Anterior</button><button class="button button-secondary button-sm" data-action="page" data-view="${view}" data-url="${escapeHtml(page.next || "")}" ${page.next ? "" : "disabled"}>Próxima</button></span></div>`;
}

function showEmpty(message) {
  const empty = root.querySelector("[data-empty-state]");
  root.querySelector("[data-table-wrap]").hidden = true; empty.classList.remove("hidden");
  empty.innerHTML = `<span class="icon-wrap">${icon("info")}</span><p>${escapeHtml(message)}</p><button class="button button-secondary button-sm" data-action="new-equipment">${icon("plus")}Novo equipamento</button>`;
  root.querySelector("[data-pagination]").innerHTML = "";
}

function bind(element) {
  if (element.dataset.bound === "true") return;
  element.dataset.bound = "true";
  element.addEventListener("submit", (event) => { if (event.target.matches("[data-collection-search]")) { event.preventDefault(); state.search.equipamentos = new FormData(event.target).get("q") || ""; render(); } });
  element.addEventListener("click", (event) => { const action = event.target.closest("[data-action]"); if (!action) return; if (action.dataset.action === "new-equipment") openCreate(); if (action.dataset.action === "equipment-detail") openDetail(action.dataset.id); if (action.dataset.action === "refresh-screen") render(); if (action.dataset.action === "page" && action.dataset.url) render({ pageUrl: action.dataset.url }); });
}

async function openCreate() {
  if (!state.cache.clientes.length) state.cache.clientes = unwrap(await api("/clientes/?ativo=1")).results;
  openModal("Novo equipamento", "Vincule o equipamento ao cliente correto para manter o histórico completo.", `<form id="equipment-form"><div class="form-grid"><div class="field full"><label>Cliente <span>*</span></label><select name="cliente" required>${state.cache.clientes.map((item) => `<option value="${item.id}">${escapeHtml(item.nome)}</option>`).join("")}</select></div><div class="field"><label>Categoria <span>*</span></label><input name="categoria" required /></div><div class="field"><label>Marca <span>*</span></label><input name="marca" required /></div><div class="field"><label>Modelo <span>*</span></label><input name="modelo" required /></div><div class="field"><label>Número de série</label><input name="numero_serie" /></div></div></form>`, `<button class="button button-secondary" data-action="close-modal">Cancelar</button><button class="button button-primary" form="equipment-form" type="submit">${icon("check")}Salvar</button>`);
  document.getElementById("equipment-form").addEventListener("submit", async (event) => { event.preventDefault(); try { await api("/equipamentos/", jsonOptions(Object.fromEntries(new FormData(event.currentTarget).entries()))); closeModal(); showToast("Equipamento cadastrado.", "success"); await render(); } catch (error) { if (!handleAuthError(error)) showToast(error.message, "error"); } });
}

function openDetail(id) { const item = state.cache.equipamentos.find((equipment) => String(equipment.id) === String(id)); if (!item) return; openModal(`${item.marca} ${item.modelo}`, "Dados do equipamento", `<div class="detail-list"><div><div class="detail-item-label">Categoria</div><div class="detail-item-value">${escapeHtml(item.categoria)}</div></div><div><div class="detail-item-label">Cliente</div><div class="detail-item-value">${escapeHtml(item.cliente_nome)}</div></div><div><div class="detail-item-label">Número de série</div><div class="detail-item-value">${escapeHtml(item.numero_serie || "—")}</div></div><div><div class="detail-item-label">Cadastrado em</div><div class="detail-item-value">${formatDateTime(item.criado_em)}</div></div></div>`, '<button class="button button-secondary" data-action="close-modal">Fechar</button>'); }

render();










