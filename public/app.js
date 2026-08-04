const messages = document.querySelector("#messages");
const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const sendButton = document.querySelector("#sendButton");
const statusLabel = document.querySelector("#connectionStatus");
const settingsDialog = document.querySelector("#settingsDialog");
const accessTokenInput = document.querySelector("#accessToken");

const sessionKey = "hello-agent-session";
const tokenKey = "hello-agent-access-token";
const requestTimeoutMs = 30000;
let requestInFlight = false;
let sessionId = localStorage.getItem(sessionKey) || crypto.randomUUID();
localStorage.setItem(sessionKey, sessionId);
accessTokenInput.value = localStorage.getItem(tokenKey) || "";

function addMessage(text, role, extraClass = "") {
  const article = document.createElement("article");
  article.className = `message ${role} ${extraClass}`.trim();
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  article.appendChild(bubble);
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

function authHeaders() {
  const token = localStorage.getItem(tokenKey);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health", { cache: "no-store" });
    const health = await response.json();
    if (!health.gemini_configured) statusLabel.textContent = "Configuração pendente";
    else if (health.bridge_connected) statusLabel.textContent = "Online • computador conectado";
    else statusLabel.textContent = "Online • computador desconectado";
  } catch {
    statusLabel.textContent = "Sem conexão";
  }
}

async function sendMessage(message) {
  if (requestInFlight) return;
  requestInFlight = true;
  addMessage(message, "user");
  const pending = addMessage("Pensando…", "assistant", "pending");
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), requestTimeoutMs);
  sendButton.disabled = true;
  input.disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ message, session_id: sessionId }),
      signal: controller.signal,
    });
    const raw = await response.text();
    let payload;
    try {
      payload = JSON.parse(raw);
    } catch {
      payload = { detail: raw || `Erro HTTP ${response.status}` };
    }
    if (!response.ok) throw new Error(payload.detail || "Não foi possível responder.");
    pending.querySelector(".bubble").textContent = payload.reply;
  } catch (error) {
    const messageText = error.name === "AbortError"
      ? "A resposta demorou mais de 30 segundos. Tente novamente em um minuto."
      : `Erro: ${error.message}`;
    pending.querySelector(".bubble").textContent = messageText;
  } finally {
    window.clearTimeout(timeoutId);
    pending.classList.remove("pending");
    requestInFlight = false;
    sendButton.disabled = false;
    input.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (requestInFlight) return;
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  input.style.height = "auto";
  sendMessage(message);
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 144)}px`;
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !requestInFlight) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelector("#settingsButton").addEventListener("click", () => settingsDialog.showModal());
document.querySelector("#saveSettingsButton").addEventListener("click", () => {
  localStorage.setItem(tokenKey, accessTokenInput.value.trim());
});
document.querySelector("#newChatButton").addEventListener("click", async () => {
  try {
    await fetch(`/api/sessions/${encodeURIComponent(sessionId)}`, { method: "DELETE", headers: authHeaders() });
  } finally {
    sessionId = crypto.randomUUID();
    localStorage.setItem(sessionKey, sessionId);
    messages.replaceChildren();
    addMessage("Nova conversa iniciada. Como posso ajudar?", "assistant");
    settingsDialog.close();
  }
});

if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js");
checkHealth();
