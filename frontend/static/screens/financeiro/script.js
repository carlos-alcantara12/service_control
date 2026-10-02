import { bindShell, api, formatNumber, escapeHtml, formatDateTime, formatMoney, handleAuthError, icon, state, statusTag, unwrap } from "/static/shared/core.js";

const root=document.querySelector("[data-screen-slot]");bindShell();

export async function render(options={}) {
  setLoading();
  try { const data=unwrap(await api(options.pageUrl||"/pagamentos/?page=1"));state.pages.financeiro={next:data.next||"",previous:data.previous||""};const term=String(state.search.financeiro||"").toLowerCase();const records=term?data.results.filter((item)=>`${item.identificador_operacao} ${item.referencia||""} ${item.ordem} ${item.registrado_por_nome||""}`.toLowerCase().includes(term)):data.results;renderRows(records,term?records.length:data.count); }
  catch(error){if(handleAuthError(error))return;showEmpty(error.message);} bind(root);
}

function setLoading(){root.querySelector("[data-table-wrap]").hidden=true;const empty=root.querySelector("[data-empty-state]");empty.classList.remove("hidden");empty.innerHTML='<div class="page-loading"><span class="spinner" role="status" aria-label="Carregando pagamentos"></span></div>';}
function renderRows(records,count){const table=root.querySelector("[data-table-wrap]"),body=root.querySelector("[data-table-body]"),empty=root.querySelector("[data-empty-state]");root.querySelector("#search-financeiro").value=state.search.financeiro||"";if(!records.length){showEmpty("Nenhum pagamento registrado.");return;}body.innerHTML=records.map((item)=>`<tr><td class="primary-cell">${escapeHtml(item.identificador_operacao)}<div class="muted-cell" style="margin-top:4px">${escapeHtml(item.referencia||"Sem referência")}</div></td><td><button class="button-ghost row-action" data-action="order-detail" data-id="${item.ordem}">OS #${escapeHtml(item.ordem)}</button></td><td>${escapeHtml(item.registrado_por_nome||"—")}</td><td class="muted-cell">${escapeHtml(item.forma_display||item.forma)}</td><td>${statusTag(item.situacao,item.situacao_display)}</td><td class="muted-cell">${formatDateTime(item.pago_em)}</td><td class="right">${formatMoney(item.valor)}</td></tr>`).join("");table.hidden=false;empty.classList.add("hidden");updatePagination("financeiro",count,records.length);}
function updatePagination(view, count, loaded) {
  const page = state.pages[view] || {};
  const container = root.querySelector("[data-pagination]");
  if (!count && !page.next && !page.previous) { container.innerHTML = ""; return; }
  container.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 18px;border-top:1px solid var(--border);color:var(--muted);font-size:11px"><span>${formatNumber(loaded)} de ${formatNumber(count)} registros</span><span style="display:flex;gap:6px"><button class="button button-secondary button-sm" data-action="page" data-view="${view}" data-url="${escapeHtml(page.previous || "")}" ${page.previous ? "" : "disabled"}>Anterior</button><button class="button button-secondary button-sm" data-action="page" data-view="${view}" data-url="${escapeHtml(page.next || "")}" ${page.next ? "" : "disabled"}>Próxima</button></span></div>`;
}

function showEmpty(message){const empty=root.querySelector("[data-empty-state]");root.querySelector("[data-table-wrap]").hidden=true;empty.classList.remove("hidden");empty.innerHTML=`<span class="icon-wrap">${icon("info")}</span><p>${escapeHtml(message)}</p>`;root.querySelector("[data-pagination]").innerHTML="";}
function bind(element){if(element.dataset.bound==="true")return;element.dataset.bound="true";element.addEventListener("submit",(event)=>{if(!event.target.matches("[data-collection-search]"))return;event.preventDefault();state.search.financeiro=new FormData(event.target).get("q")||"";render();});element.addEventListener("click",async(event)=>{const action=event.target.closest("[data-action]");if(action?.dataset.action==="order-detail")(await import("/static/screens/ordens/script.js")).openOrderDetail(action.dataset.id);if(action?.dataset.action==="refresh-screen")render();if(action?.dataset.action==="page"&&action.dataset.url)render({pageUrl:action.dataset.url});});}
render();







