import { bindShell, api, escapeHtml, formatDate, formatMoney, formatNumber, handleAuthError, icon, state, statusTag } from "../shared/core.js";

const root = document.querySelector("[data-screen-slot]");
bindShell();

export async function render() {
  if (!root) return;
  const [operational, financial, ordersResult] = await Promise.allSettled([
    api("/relatorios/operacional/"),
    api("/relatorios/financeiro/"),
    api("/ordens/?page=1"),
  ]);
  if (operational.status === "rejected" && handleAuthError(operational.reason)) return;

  const op = operational.status === "fulfilled" ? operational.value : {};
  const fin = financial.status === "fulfilled" ? financial.value : {};
  const orders = ordersResult.status === "fulfilled"
    ? (Array.isArray(ordersResult.value) ? ordersResult.value : ordersResult.value.results || [])
    : [];
  const counts = op.ordens_por_situacao || {};
  const active = Object.entries(counts)
    .filter(([code]) => !["ENTREGUE", "CANCELADA"].includes(code))
    .reduce((total, [, value]) => total + Number(value || 0), 0);
  const overdue = Number(op.ordens_atrasadas || 0);
  const firstName = (state.user?.nome || "equipe").split(" ")[0];
  const firstNameElement = root.querySelector("[data-dashboard-first-name]");
  if (firstNameElement) firstNameElement.textContent = firstName;

  updateStat("active", formatNumber(active), active ? `${formatNumber(active)} em acompanhamento` : "Sem ordens em andamento", active ? "positive" : "");
  updateStat("overdue", formatNumber(overdue), overdue ? "Requer atenção" : "Dentro do prazo", overdue ? "attention" : "positive");
  updateStat("received", fin.valor_recebido != null ? formatMoney(fin.valor_recebido) : "—", financial.status === "fulfilled" ? "Consolidado do período atual" : "Relatório restrito ao gerente", financial.status === "fulfilled" ? "positive" : "");
  updateStat("pending", fin.saldo_pendente != null ? formatMoney(fin.saldo_pendente) : "—", financial.status === "fulfilled" ? "A receber das ordens atuais" : "Acesso de gerente necessário", financial.status === "fulfilled" ? "attention" : "");

  const ordersElement = root.querySelector("[data-dashboard-orders]");
  const flowElement = root.querySelector("[data-dashboard-flow]");
  if (ordersElement) ordersElement.innerHTML = renderRecentOrders(orders);
  if (flowElement) flowElement.innerHTML = renderFlow(counts);
  bind(root);
}

function updateStat(name, value, note, tone) {
  const card = root.querySelector(`[data-stat="${name}"]`);
  if (!card) return;
  card.querySelector("[data-stat-value]").textContent = value;
  const noteElement = card.querySelector("[data-stat-note]");
  noteElement.textContent = note;
  noteElement.className = `stat-meta ${tone}`;
}

function renderRecentOrders(orders) {
  if (!orders.length) return `<div class="empty-state"><span class="icon-wrap">${icon("info")}</span><p>Nenhuma ordem de serviço encontrada.</p></div>`;
  return `<table class="data-table"><thead><tr><th>Ordem</th><th>Cliente</th><th>Status</th><th>Previsão</th><th class="right">Saldo</th><th></th></tr></thead><tbody>${orders.map((order) => `<tr><td class="primary-cell"><button class="button-ghost row-action" data-action="order-detail" data-id="${order.id}">${escapeHtml(order.numero || `OS #${order.id}`)}</button><div class="muted-cell" style="margin-top:4px">${escapeHtml(order.equipamento_descricao || "Equipamento não informado")}</div></td><td>${escapeHtml(order.cliente_nome || `Cliente #${order.cliente}`)}</td><td>${statusTag(order.situacao, order.situacao_display)}</td><td class="muted-cell">${formatDate(order.previsao_entrega)}</td><td class="right">${formatMoney(order.saldo_pendente)}</td><td class="right">${icon("chevronRight")}</td></tr>`).join("")}</tbody></table>`;
}

function renderFlow(counts) {
  const flow = ["RECEBIDA", "EM_DIAGNOSTICO", "AGUARDANDO_APROVACAO", "EM_REPARO", "EM_TESTES", "PRONTA_ENTREGA", "ENTREGUE"]
    .map((code) => ({ code, label: code.toLowerCase().replace(/_/g, " "), value: Number(counts[code] || 0) }));
  const max = Math.max(...flow.map((item) => item.value), 1);
  return flow.map((item) => `<div class="progress-row"><div class="progress-label"><span>${escapeHtml(item.label.replace(/\b\w/g, (letter) => letter.toUpperCase()))}</span><strong>${formatNumber(item.value)}</strong></div><div class="progress-track"><div class="progress-fill ${item.code === "ENTREGUE" ? "success" : item.code === "AGUARDANDO_APROVACAO" ? "warning" : ""}" style="width:${Math.max(item.value / max * 100, item.value ? 8 : 0)}%"></div></div></div>`).join("");
}

function bind(element) {
  if (element.dataset.bound === "true") return;
  element.dataset.bound = "true";
  element.addEventListener("click", async (event) => {
    const action = event.target.closest("[data-action]");
    if (action?.dataset.action === "new-order") return (await import("../ordens/script.js")).openCreateModal("ordem");
    if (action?.dataset.action === "order-detail") return (await import("../ordens/script.js")).openOrderDetail(action.dataset.id);
  });
}

render();
