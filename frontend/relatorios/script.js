import { bindShell, api, escapeHtml, formatMoney, formatNumber, handleAuthError, icon, statusTag } from "../shared/core.js";

const root = document.querySelector("[data-screen-slot]");
bindShell();

export async function render() {
  const [financial, operational] = await Promise.allSettled([
    api("/relatorios/financeiro/"),
    api("/relatorios/operacional/"),
  ]);
  if (financial.status === "rejected" && operational.status === "rejected") {
    if (handleAuthError(financial.reason)) return;
    showMessage(root.querySelector("[data-report-status]"), "Não foi possível carregar os relatórios.");
    showMessage(root.querySelector("[data-report-technicians]"), "Não foi possível carregar os relatórios.");
    return;
  }

  const fin = financial.status === "fulfilled" ? financial.value : null;
  const op = operational.status === "fulfilled" ? operational.value : null;
  if (op) renderOperational(op);
  else showMessage(root.querySelector("[data-report-status]"), "Dados operacionais indisponíveis.");
  if (fin) renderFinancial(fin);
  else {
    root.querySelector("[data-report-approved]").textContent = "Restrito";
    root.querySelector("[data-report-received]").textContent = "Restrito";
    root.querySelector("[data-report-balance]").textContent = "Restrito";
    root.querySelector("[data-report-note=approved]").textContent = "Disponível para gerentes";
  }
}

function renderOperational(data) {
  const overdue = root.querySelector("[data-report=overdue]");
  overdue.textContent = formatNumber(data.ordens_atrasadas);
  overdue.className = `report-card-value ${Number(data.ordens_atrasadas) ? "warning" : "success"}`;
  root.querySelector("[data-report=average]").innerHTML = `${escapeHtml(data.tempo_medio_atendimento_dias)} <small style="font-size:12px;font-weight:500">dias</small>`;
  root.querySelector("[data-report=pickup]").textContent = formatNumber(data.equipamentos_aguardando_retirada);

  const counts = data.ordens_por_situacao || {};
  const max = Math.max(...Object.values(counts).map(Number), 1);
  const rows = Object.entries(counts).map(([code, value]) => `<div class="progress-row"><div class="progress-label"><span>${escapeHtml(labelize(code))}</span><strong>${formatNumber(value)}</strong></div><div class="progress-track"><div class="progress-fill" style="width:${Math.min(Number(value) / max * 100, 100)}%"></div></div></div>`).join("");
  root.querySelector("[data-report-status]").innerHTML = rows || `<div class="empty-state"><span class="icon-wrap">${icon("info")}</span><p>Sem dados operacionais.</p></div>`;

  const technicians = (data.servicos_por_tecnico || []).map((item) => `<tr><td class="primary-cell">${escapeHtml(item.tecnico_nome)}</td><td class="right">${formatNumber(item.servicos_concluidos)}</td></tr>`).join("");
  root.querySelector("[data-report-technicians]").innerHTML = technicians
    ? `<table class="data-table"><thead><tr><th>Técnico</th><th class="right">Serviços</th></tr></thead><tbody>${technicians}</tbody></table>`
    : `<div class="empty-state"><span class="icon-wrap">${icon("info")}</span><p>Ainda não há serviços concluídos.</p></div>`;
}

function renderFinancial(data) {
  root.querySelector("[data-report-approved]").textContent = formatNumber(data.orcamentos_aprovados);
  root.querySelector("[data-report-received]").textContent = formatMoney(data.valor_recebido);
  root.querySelector("[data-report-balance]").textContent = formatMoney(data.saldo_pendente);
  root.querySelector("[data-report-note=approved]").textContent = `${formatMoney(data.valor_aprovado)} aprovados`;
}

function showMessage(element, message) {
  element.innerHTML = `<div class="empty-state"><span class="icon-wrap">${icon("info")}</span><p>${escapeHtml(message)}</p></div>`;
}

function labelize(value) { return String(value || "").toLowerCase().replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase()); }

render();

