import { api, saveUser } from "../shared/core.js";

const form = document.getElementById("login-form");
const errorBox = document.getElementById("login-error");
const submitButton = form?.querySelector("button[type=submit]");

function showError(message) {
  if (!errorBox) return;
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}

async function submit(event) {
  event.preventDefault();
  errorBox?.classList.add("hidden");
  if (submitButton) { submitButton.disabled = true; submitButton.textContent = "Entrando..."; }
  try {
    const credentials = Object.fromEntries(new FormData(form).entries());
    saveUser(await api("/login/", { method: "POST", body: JSON.stringify(credentials) }));
    window.location.href = "../dashboard/";
  } catch (error) {
    showError(error.message || "Não foi possível entrar. Verifique suas credenciais.");
    if (submitButton) { submitButton.disabled = false; submitButton.textContent = "Entrar"; }
  }
}

form?.addEventListener("submit", submit);

