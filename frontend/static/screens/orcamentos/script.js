import { bindShell, api, escapeHtml, formatNumber, formatDate, formatDateTime, formatMoney, handleAuthError, icon, state, statusTag, unwrap } from "/static/shared/core.js";

const root = document.querySelector("[data-screen-slot]");
bindShell();

export async function render(options = {}) {
  const term = encodeURIComponent(state.search.orcamentos || "");
  const filter = state.filters.orcamentos || "";
  setLoading();
  try {
    const data = unwrap(await api(options.pageUrl || `/orcamentos/?page=1${term ? `&q=${term}` : ""}${filter ? `&situacao=${filter}` : ""}`));
    state.pages.orcamentos = { next: data.next || "", previous: data.previous || "" };
    renderRows(data.results, data.count);
  } catch (error) { if (handleAuthError(error)) return; showEmpty(error.message); }
  bind(root);
}

function setLoading() { root.querySelector("[data-table-wrap]").hidden = true; const empty = root.querySelector("[data-empty-state]"); empty.classList.remove("hidden"); empty.innerHTML = '<div class="page-loading"><span class="spinner" role="status" aria-label="Carregando orçamentos"></span></div>'; }

function renderRows(records, count) {
  const table=root.querySelector("[data-table-wrap]"), body=root.querySelector("[data-table-body]"), empty=root.querySelector("[data-empty-state]");
  root.querySelector("#search-orcamentos").value=state.search.orcamentos||""; root.querySelector("[data-budget-filter]").value=state.filters.orcamentos||"";
  if(!records.length){showEmpty("Nenhum orçamento encontrado.");return;}
  body.innerHTML=records.map((item)=>`<tr><td class="primary-cell">Versão ${escapeHtml(item.versao)}<div class="muted-cell" style="margin-top:4px">${formatDateTime(item.criado_em)}</div></td><td><button class="button-ghost row-action" data-action="order-detail" data-id="${item.ordem}">OS #${escapeHtml(item.ordem)}</button></td><td>${escapeHtml(item.criador_nome||"—")}</td><td>${statusTag(item.situacao,item.situacao_display)}</td><td class="muted-cell">${formatDate(item.valido_ate)}</td><td class="right">${formatMoney(item.total)}</td><td class="right">${icon("chevronRight")}</td></tr>`).join("");
  table.hidden=false;empty.classList.add("hidden");updatePagination("orcamentos",count,records.length);
}

function updatePagination(view, count, loaded) {
  const page = state.pages[view] || {};
  const container = root.querySelector("[data-pagination]");
  if (!count && !page.next && !page.previous) { container.innerHTML = ""; return; }
  container.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 18px;border-top:1px solid var(--border);color:var(--muted);font-size:11px"><span>${formatNumber(loaded)} de ${formatNumber(count)} registros</span><span style="display:flex;gap:6px"><button class="button button-secondary button-sm" data-action="page" data-view="${view}" data-url="${escapeHtml(page.previous || "")}" ${page.previous ? "" : "disabled"}>Anterior</button><button class="button button-secondary button-sm" data-action="page" data-view="${view}" data-url="${escapeHtml(page.next || "")}" ${page.next ? "" : "disabled"}>Próxima</button></span></div>`;
}

function showEmpty(message){const empty=root.querySelector("[data-empty-state]");root.querySelector("[data-table-wrap]").hidden=true;empty.classList.remove("hidden");empty.innerHTML=`<span class="icon-wrap">${icon("info")}</span><p>${escapeHtml(message)}</p>`;root.querySelector("[data-pagination]").innerHTML="";}

function bind(element){if(element.dataset.bound==="true")return;element.dataset.bound="true";element.addEventListener("submit",(event)=>{if(!event.target.matches("[data-collection-search]"))return;event.preventDefault();state.search.orcamentos=new FormData(event.target).get("q")||"";render();});element.addEventListener("change",(event)=>{if(event.target.matches("[data-budget-filter]")){state.filters.orcamentos=event.target.value;render();}});element.addEventListener("click",async(event)=>{const action=event.target.closest("[data-action]");if(action?.dataset.action==="order-detail")(await import("/static/screens/ordens/script.js")).openOrderDetail(action.dataset.id);if(action?.dataset.action==="refresh-screen")render();if(action?.dataset.action==="page"&&action.dataset.url)render({pageUrl:action.dataset.url});});}

render();













