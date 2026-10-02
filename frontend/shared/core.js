const storageKey = "serviceflow.user";

export const state = {
  user: readUser(),
  search: {},
  filters: {},
  pages: {},
  cache: { clientes: [], equipamentos: [], ordens: [] },
};

const icons = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  clipboard: '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4.5V3h6v1.5M8 9h8M8 13h8M8 17h5"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  monitor: '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
  fileText: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h6"/>',
  wallet: '<path d="M20 7V5a2 2 0 0 0-2-2H5a3 3 0 0 0 0 6h16v12H5a3 3 0 0 1-3-3V6"/><path d="M16 14h.01"/>',
  chart: '<path d="M3 3v18h18"/><path d="m7 16 4-5 3 3 5-7"/>',
  settings: '<path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"/><path d="m19.4 15 .1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.9 1.9 0 0 0-3.2 1.4v.3a2 2 0 1 1-4 0v-.2A1.9 1.9 0 0 0 6.2 18l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.9 1.9 0 0 0 2 12a1.9 1.9 0 0 0 1.4-3.2l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.9 1.9 0 0 0 9.5 4h.1a2 2 0 1 1 4 0v.2A1.9 1.9 0 0 0 16.8 6l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1A1.9 1.9 0 0 0 21 12a1.9 1.9 0 0 0-1.6 3Z"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  chevronRight: '<path d="m9 18 6-6-6-6"/>',
  arrowRight: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  alert: '<path d="M10.3 3.7 2.6 17a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 3.7a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  x: '<path d="m6 6 12 12M18 6 6 18"/>',
  more: '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
  refresh: '<path d="M20 11a8.1 8.1 0 0 0-14.6-3L3 11m0-5v5h5M4 13a8.1 8.1 0 0 0 14.6 3L21 13m0 5v-5h-5"/>',
  eye: '<path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.5"/>',
  logout: '<path d="M10 17l5-5-5-5M15 12H3M21 19V5a2 2 0 0 0-2-2h-6"/>',
  userPlus: '<path d="M15 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8" cy="7" r="4"/><path d="M19 8v6M16 11h6"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
  alertCircle: '<circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/>',
  dollar: '<circle cx="12" cy="12" r="9"/><path d="M15 8.5c-.7-.6-1.7-1-3-1-1.7 0-3 .8-3 2s1.2 2 3 2 3 .8 3 2-1.3 2-3 2c-1.3 0-2.3-.4-3-1M12 5v14"/>',
};

const localApiHost = ["localhost", "127.0.0.1"].includes(window.location.hostname)
  ? window.location.hostname
  : "127.0.0.1";
export const API_BASE = window.SERVICEFLOW_API_BASE || `http://${localApiHost}:8000/api`;
const API_ORIGIN = new URL(API_BASE, window.location.href).origin;
export function icon(name, className = "") { return `<span class="icon ${className}" aria-hidden="true"><svg viewBox="0 0 24 24">${icons[name] || icons.info}</svg></span>`; }
export function readUser() { try { return JSON.parse(localStorage.getItem(storageKey) || "null"); } catch (_) { return null; } }
export function saveUser(user) { state.user = user; localStorage.setItem(storageKey, JSON.stringify(user)); }
export function clearUser() { state.user = null; localStorage.removeItem(storageKey); }
export function escapeHtml(value) { return String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;"); }
export function initials(name) { return String(name || "SF").split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase(); }
export function formatMoney(value) { return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(value || 0)); }
export function formatNumber(value) { return new Intl.NumberFormat("pt-BR").format(Number(value || 0)); }
export function formatDate(value) { if (!value) return "—"; const date = new Date(`${String(value).slice(0, 10)}T12:00:00`); return Number.isNaN(date.getTime()) ? String(value) : new Intl.DateTimeFormat("pt-BR").format(date); }
export function formatDateTime(value) { if (!value) return "—"; const date = new Date(value); return Number.isNaN(date.getTime()) ? String(value) : new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(date); }
export function labelize(value) { return String(value || "").toLowerCase().replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase()); }
export function statusClass(value) { const code = String(value || "").toUpperCase(); if (["ENTREGUE", "APROVADO", "QUITADA", "CONFIRMADO", "PRONTA_ENTREGA"].includes(code)) return "status-success"; if (["CANCELADA", "RECUSADO", "ESTORNADA", "CANCELADO"].includes(code)) return "status-danger"; if (["AGUARDANDO_APROVACAO", "AGUARDANDO_PECA", "EXPIRADO", "PENDENTE", "PARCIAL"].includes(code)) return "status-warning"; if (["EM_REPARO", "EM_DIAGNOSTICO", "EM_TESTES", "ENVIADO", "RECEBIDA"].includes(code)) return "status-info"; return "status-neutral"; }
export function statusTag(code, display) { return `<span class="status ${statusClass(code)}">${escapeHtml(display || labelize(code) || "Sem status")}</span>`; }
export function unwrap(payload) { if (Array.isArray(payload)) return { results: payload, count: payload.length }; return { results: payload?.results || [], count: payload?.count ?? payload?.results?.length ?? 0, next: payload?.next, previous: payload?.previous }; }
export function loadingMarkup() { return `<div class="page-loading"><span class="spinner" role="status" aria-label="Carregando"></span></div>`; }
export function emptyMarkup(message, action = "") { return `<div class="empty-state"><span class="icon-wrap">${icon("info")}</span><p>${escapeHtml(message)}</p>${action ? `<div style="margin-top:14px">${action}</div>` : ""}</div>`; }

function getCookie(name) { const prefix = `${name}=`; const part = document.cookie.split(";").map((item) => item.trim()).find((item) => item.startsWith(prefix)); return part ? decodeURIComponent(part.slice(prefix.length)) : ""; }
async function ensureCsrf() { if (!getCookie("csrftoken")) await fetch(`${API_ORIGIN}/admin/login/`, { credentials: "include" }); }
export class ApiError extends Error { constructor(message, status) { super(message); this.status = status; } }
export async function api(path, options = {}) {
  const method = String(options.method || "GET").toUpperCase();
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) await ensureCsrf();
  const headers = { Accept: "application/json", ...(options.headers || {}) };
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) { headers["X-CSRFToken"] = getCookie("csrftoken"); if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json"; }
  const url = /^https?:\/\//i.test(path) ? path : `${API_BASE}${path}`;
  const response = await fetch(url, { credentials: "include", ...options, method, headers });
  const type = response.headers.get("content-type") || "";
  const payload = type.includes("json") ? await response.json().catch(() => ({})) : await response.text();
  if (!response.ok) { const detail = typeof payload === "string" ? payload : payload.detail || Object.values(payload || {}).flat().join(" ") || "Não foi possível concluir a solicitação."; throw new ApiError(detail, response.status); }
  return payload;
}
export function jsonOptions(body) { return { method: "POST", body: JSON.stringify(body) }; }

export function bindShell() {
  if (window.__serviceflowShellBound) return;
  window.__serviceflowShellBound = true;
  const user = state.user || {};
  const name = user.nome || "Usuário";
  const role = user.perfil_display || labelize(user.perfil) || "Equipe";
  const avatar = initials(name);
  document.querySelector("[data-admin-only]")?.toggleAttribute("hidden", user.perfil !== "GERENTE");
  ["sidebar-name", "top-name"].forEach((id) => { const element = document.getElementById(id); if (element) element.textContent = name; });
  ["sidebar-role", "top-role"].forEach((id) => { const element = document.getElementById(id); if (element) element.textContent = role; });
  ["sidebar-avatar", "top-avatar"].forEach((id) => { const element = document.getElementById(id); if (element) element.textContent = avatar; });
  document.addEventListener("click", async (event) => {
    const action = event.target.closest("[data-action]");
    if (!action) return;
    if (action.dataset.action === "toggle-nav") { document.body.classList.toggle("nav-open"); return; }
    if (action.dataset.action === "notifications") { showToast("Não há novas notificações."); return; }
    if (action.dataset.action === "close-modal") { closeModal(); return; }
    if (action.dataset.action === "logout") {
      try { await api("/logout/", { method: "POST" }); } catch (_) { /* a sessão local também deve ser encerrada */ }
      clearUser(); window.location.href = "../login/";
    }
  });
  document.getElementById("global-search-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const query = new FormData(event.currentTarget).get("q") || "";
    window.location.href = `../ordens/${query ? `?q=${encodeURIComponent(query)}` : ""}`;
  });
}

export function showToast(message, type = "info") { let stack = document.getElementById("toast-stack"); if (!stack) { stack = document.createElement("div"); stack.id = "toast-stack"; stack.className = "toast-stack"; document.body.appendChild(stack); } const toast = document.createElement("div"); toast.className = `toast ${type}`; toast.innerHTML = `${icon(type === "error" ? "alertCircle" : type === "success" ? "check" : "info")}<span>${escapeHtml(message)}</span>`; stack.appendChild(toast); window.setTimeout(() => toast.remove(), 4200); }
export function openModal(title, description, body, footer = "", wide = false) { closeModal(); const wrapper = document.createElement("div"); wrapper.className = "modal-backdrop"; wrapper.id = "modal-backdrop"; wrapper.innerHTML = `<section class="modal ${wide ? "modal-wide" : ""}" role="dialog" aria-modal="true" aria-labelledby="modal-title"><div class="modal-header"><div><h2 class="modal-title" id="modal-title">${escapeHtml(title)}</h2>${description ? `<p class="modal-description">${escapeHtml(description)}</p>` : ""}</div><button class="close-button" data-action="close-modal" aria-label="Fechar">${icon("x")}</button></div><div class="modal-body">${body}</div>${footer ? `<div class="modal-footer">${footer}</div>` : ""}</section>`; document.body.appendChild(wrapper); wrapper.addEventListener("click", (event) => { if (event.target === wrapper) closeModal(); }); wrapper.querySelector("input, select, textarea, button")?.focus(); }
export function closeModal() { document.getElementById("modal-backdrop")?.remove(); }
export function handleAuthError(error) { if (error?.status === 401 || error?.status === 403) { clearUser(); window.location.href = "../login/"; return true; } return false; }


