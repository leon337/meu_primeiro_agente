const messages = document.querySelector("#messages");
const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const sendButton = document.querySelector("#sendButton");
const micButton = document.querySelector("#micButton");
const statusLabel = document.querySelector("#connectionStatus");
const settingsDialog = document.querySelector("#settingsDialog");
const accessTokenInput = document.querySelector("#accessToken");
const voiceOutputInput = document.querySelector("#voiceOutput");
const missionIdInput = document.querySelector("#missionId");

const sessionKey = "hello-agent-session";
const tokenKey = "hello-agent-access-token";
const voiceKey = "hello-agent-voice-output";
const missionKey = "hello-agent-active-mission";
let sessionId = localStorage.getItem(sessionKey) || crypto.randomUUID();
localStorage.setItem(sessionKey, sessionId);
accessTokenInput.value = localStorage.getItem(tokenKey) || "";
voiceOutputInput.checked = localStorage.getItem(voiceKey) === "1";
missionIdInput.value = localStorage.getItem(missionKey) || "";

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

function speak(text) {
  if (!voiceOutputInput.checked || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text.slice(0, 1200));
  utterance.lang = "pt-BR";
  utterance.rate = 1;
  window.speechSynthesis.speak(utterance);
}

async function parseResponse(response) {
  const raw = await response.text();
  try {
    return JSON.parse(raw);
  } catch {
    return { detail: raw || `Erro HTTP ${response.status}` };
  }
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const health = await response.json();
    if (!health.gemini_configured) statusLabel.textContent = "Configuração pendente";
    else if (health.bridge_connected && health.executive_configured) statusLabel.textContent = "Online • computador e runtime conectados";
    else if (health.bridge_connected) statusLabel.textContent = "Online • computador conectado";
    else statusLabel.textContent = "Online • computador desconectado";
  } catch {
    statusLabel.textContent = "Sem conexão";
  }
}

async function sendMessage(message) {
  addMessage(message, "user");
  const pending = addMessage("Pensando…", "assistant", "pending");
  sendButton.disabled = true;
  micButton.disabled = true;
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
    const payload = await parseResponse(response);
    if (!response.ok) throw new Error(payload.detail || "Não foi possível responder.");
    pending.querySelector(".bubble").textContent = payload.reply;
    pending.classList.remove("pending");
    speak(payload.reply);
  } catch (error) {
    pending.querySelector(".bubble").textContent = `Erro: ${error.message}`;
  } finally {
    sendButton.disabled = false;
    micButton.disabled = false;
    input.focus();
  }
}

async function getMissionStatus(missionId) {
  if (!missionId) throw new Error("Informe o identificador da missão.");
  const response = await fetch(`/api/missions/${encodeURIComponent(missionId)}`, { headers: authHeaders() });
  const payload = await parseResponse(response);
  if (!response.ok) throw new Error(payload.detail || "Não foi possível consultar a missão.");
  const text = `Missão ${payload.mission_id}: ${payload.status}. Parada de emergência: ${payload.emergency_stopped ? "sim" : "não"}.`;
  addMessage(text, "assistant");
  speak(text);
}

async function emergencyStop(missionId, reason = "Parada solicitada pelo usuário") {
  if (!missionId) throw new Error("Informe o identificador da missão.");
  const response = await fetch(`/api/missions/${encodeURIComponent(missionId)}/emergency-stop`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ actor: "Leandro", reason }),
  });
  const payload = await parseResponse(response);
  if (!response.ok) throw new Error(payload.detail || "Não foi possível parar a missão.");
  const text = `Parada de emergência registrada para ${payload.mission_id}.`;
  addMessage(text, "assistant");
  speak(text);
}

async function routeVoiceCommand(text) {
  const statusMatch = text.match(/^(?:status|situação) da missão\s+(.+)$/i);
  const stopMatch = text.match(/^(?:parar|pare a) missão\s+(.+)$/i);
  if (statusMatch) {
    missionIdInput.value = statusMatch[1].trim();
    localStorage.setItem(missionKey, missionIdInput.value);
    await getMissionStatus(missionIdInput.value);
    return;
  }
  if (stopMatch) {
    missionIdInput.value = stopMatch[1].trim();
    localStorage.setItem(missionKey, missionIdInput.value);
    await emergencyStop(missionIdInput.value, "Parada solicitada por comando de voz");
    return;
  }
  await sendMessage(text);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
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
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SpeechRecognition) {
  micButton.hidden = true;
} else {
  const recognition = new SpeechRecognition();
  recognition.lang = "pt-BR";
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.addEventListener("start", () => {
    micButton.classList.add("listening");
    statusLabel.textContent = "Ouvindo comando…";
  });
  recognition.addEventListener("end", () => {
    micButton.classList.remove("listening");
    checkHealth();
  });
  recognition.addEventListener("result", async (event) => {
    const text = event.results[0][0].transcript.trim();
    input.value = text;
    try {
      await routeVoiceCommand(text);
      input.value = "";
    } catch (error) {
      addMessage(`Erro: ${error.message}`, "assistant");
    }
  });
  recognition.addEventListener("error", (event) => {
    addMessage(`Não foi possível reconhecer a voz: ${event.error}.`, "assistant");
  });
  micButton.addEventListener("click", () => recognition.start());
}

document.querySelector("#settingsButton").addEventListener("click", () => settingsDialog.showModal());
document.querySelector("#saveSettingsButton").addEventListener("click", () => {
  localStorage.setItem(tokenKey, accessTokenInput.value.trim());
  localStorage.setItem(voiceKey, voiceOutputInput.checked ? "1" : "0");
  localStorage.setItem(missionKey, missionIdInput.value.trim());
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
document.querySelector("#missionStatusButton").addEventListener("click", async () => {
  try { await getMissionStatus(missionIdInput.value.trim()); }
  catch (error) { addMessage(`Erro: ${error.message}`, "assistant"); }
});
document.querySelector("#emergencyStopButton").addEventListener("click", async () => {
  const missionId = missionIdInput.value.trim();
  if (!missionId || !window.confirm(`Parar imediatamente a missão ${missionId}?`)) return;
  try { await emergencyStop(missionId); settingsDialog.close(); }
  catch (error) { addMessage(`Erro: ${error.message}`, "assistant"); }
});

if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js");
checkHealth();
