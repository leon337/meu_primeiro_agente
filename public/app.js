const messages = document.querySelector("#messages");
const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const sendButton = document.querySelector("#sendButton");
const micButton = document.querySelector("#micButton");
const statusLabel = document.querySelector("#connectionStatus");
const sidebarStatusDot = document.querySelector("#sidebarStatusDot");
const sidebarStatusText = document.querySelector("#sidebarStatusText");
const settingsDialog = document.querySelector("#settingsDialog");
const accessTokenInput = document.querySelector("#accessToken");
const voiceOutputInput = document.querySelector("#voiceOutput");
const missionIdInput = document.querySelector("#missionId");
const missionStatusDot = document.querySelector("#missionStatusDot");
const missionStatusText = document.querySelector("#missionStatusText");
const missionMeta = document.querySelector("#missionMeta");
const missionObjective = document.querySelector("#missionObjective");
const missionStep = document.querySelector("#missionStep");
const missionEvidence = document.querySelector("#missionEvidence");
const emergencyStopButton = document.querySelector("#emergencyStopButton");
const contextTitle = document.querySelector("#contextTitle");
const missionPanel = document.querySelector("#missionPanel");
const systemPanel = document.querySelector("#systemPanel");

const sessionKey = "hello-agent-session";
const tokenKey = "hello-agent-access-token";
const voiceKey = "hello-agent-voice-output";
const missionKey = "hello-agent-active-mission";
const requestTimeoutMs = 30000;
const terminalStepStates = new Set(["COMPLETED", "FAILED", "CANCELLED"]);

let requestInFlight = false;
let sessionId = localStorage.getItem(sessionKey) || crypto.randomUUID();
localStorage.setItem(sessionKey, sessionId);
accessTokenInput.value = localStorage.getItem(tokenKey) || "";
voiceOutputInput.checked = localStorage.getItem(voiceKey) === "1";
missionIdInput.value = localStorage.getItem(missionKey) || "";

function statusClass(element, state) {
  if (!element) return;
  element.classList.remove("checking", "healthy", "warning", "danger", "neutral");
  element.classList.add(state);
}

function setGlobalStatus(text, state = "neutral") {
  statusLabel.textContent = text;
  sidebarStatusText.textContent = text.split(" • ")[0];
  statusClass(sidebarStatusDot, state);
}

function nowLabel() {
  return new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" }).format(new Date());
}

function addMessage(text, role, extraClass = "") {
  const article = document.createElement("article");
  article.className = `message ${role} ${extraClass}`.trim();

  if (role === "assistant") {
    const identity = document.createElement("div");
    identity.className = "message-identity";
    identity.setAttribute("aria-hidden", "true");
    identity.textContent = "A";
    article.appendChild(identity);
  }

  const content = document.createElement("div");
  content.className = "message-content";

  const meta = document.createElement("div");
  meta.className = "message-meta";
  const author = document.createElement("strong");
  author.textContent = role === "assistant" ? "MESTRE" : "Você";
  const time = document.createElement("span");
  time.textContent = nowLabel();
  meta.append(author, time);

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  content.append(meta, bubble);
  article.appendChild(content);
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

function updateMessage(article, text, { error = false } = {}) {
  const bubble = article.querySelector(".bubble");
  if (bubble) bubble.textContent = text;
  article.classList.remove("pending");
  article.classList.toggle("error", error);
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

async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), requestTimeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    window.clearTimeout(timeoutId);
  }
}

function setHealthLine(name, text, state) {
  const label = document.querySelector(`#health${name}`);
  const dot = document.querySelector(`#health${name}Dot`);
  if (label) label.textContent = text;
  statusClass(dot, state);
}

function renderHealth(health) {
  const geminiOk = Boolean(health.gemini_configured);
  const bridgeConfigured = Boolean(health.bridge_configured);
  const bridgeConnected = Boolean(health.bridge_connected);
  const runtimeConfigured = Boolean(health.executive_configured);
  const whatsappConfigured = Boolean(health.whatsapp_configured);

  setHealthLine("Gemini", geminiOk ? "Configurado" : "Configuração pendente", geminiOk ? "healthy" : "warning");
  setHealthLine(
    "Bridge",
    bridgeConnected ? "Conectado" : bridgeConfigured ? "Configurado, sem conexão" : "Não configurado",
    bridgeConnected ? "healthy" : bridgeConfigured ? "warning" : "neutral",
  );
  setHealthLine("Runtime", runtimeConfigured ? "Configurado" : "Não configurado", runtimeConfigured ? "healthy" : "neutral");
  setHealthLine("Whatsapp", whatsappConfigured ? "Configurado" : "Não configurado", whatsappConfigured ? "healthy" : "neutral");
  document.querySelector("#appVersion").textContent = health.version || "—";

  if (!geminiOk) setGlobalStatus("Configuração pendente", "warning");
  else if (bridgeConnected && runtimeConfigured) setGlobalStatus("Online • computador e runtime conectados", "healthy");
  else if (bridgeConnected) setGlobalStatus("Online • computador conectado", "healthy");
  else if (bridgeConfigured) setGlobalStatus("Online • computador desconectado", "warning");
  else setGlobalStatus("Online • modo nuvem", "healthy");
}

function renderHealthFailure() {
  setHealthLine("Gemini", "Indisponível", "danger");
  setHealthLine("Bridge", "Indisponível", "danger");
  setHealthLine("Runtime", "Indisponível", "danger");
  setHealthLine("Whatsapp", "Indisponível", "danger");
  document.querySelector("#appVersion").textContent = "—";
  setGlobalStatus("Sem conexão", "danger");
}

async function checkHealth() {
  try {
    const response = await fetchWithTimeout("/api/health", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    renderHealth(await response.json());
  } catch {
    renderHealthFailure();
  }
}

function normalizeMissionPayload(payload) {
  const mission = payload && typeof payload.mission === "object" ? payload.mission : payload;
  const steps = Array.isArray(payload?.steps) ? payload.steps : Array.isArray(mission?.steps) ? mission.steps : [];
  const events = Array.isArray(payload?.events) ? payload.events : [];
  return { mission: mission || {}, steps, events };
}

function formatMissionStatus(status) {
  const labels = {
    CREATED: "Criada",
    PLANNING: "Planejando",
    READY: "Pronta",
    RUNNING: "Em execução",
    WAITING_HUMAN: "Aguardando decisão humana",
    BLOCKED: "Bloqueada",
    RECOVERING: "Em recuperação",
    COMPLETED: "Concluída",
    FAILED: "Falhou",
    CANCELLED: "Cancelada",
  };
  return labels[status] || status || "Estado desconhecido";
}

function missionStateColor(status, stopped) {
  if (stopped || ["FAILED", "CANCELLED"].includes(status)) return "danger";
  if (["WAITING_HUMAN", "BLOCKED", "RECOVERING"].includes(status)) return "warning";
  if (["READY", "RUNNING", "COMPLETED"].includes(status)) return "healthy";
  return "neutral";
}

function describeStep(step) {
  if (!step) return "Nenhuma etapa exposta pelo runtime.";
  const prefix = step.sequence ? `${step.sequence}. ` : "";
  const action = step.action || step.title || step.capability || "Etapa sem descrição";
  const state = step.status ? ` · ${formatMissionStatus(step.status)}` : "";
  return `${prefix}${action}${state}`;
}

function evidenceSummary(steps, events) {
  const evidenceCount = steps.reduce((total, step) => total + (Array.isArray(step.evidence) ? step.evidence.length : 0), 0);
  if (evidenceCount && events.length) return `${evidenceCount} evidência(s) em etapas · ${events.length} evento(s) registrados.`;
  if (evidenceCount) return `${evidenceCount} evidência(s) registrada(s) nas etapas.`;
  if (events.length) return `${events.length} evento(s) registrados pelo runtime.`;
  return "Nenhuma evidência detalhada foi exposta nesta consulta.";
}

function renderMission(payload) {
  const { mission, steps, events } = normalizeMissionPayload(payload);
  const id = mission.mission_id || missionIdInput.value.trim();
  const status = String(mission.status || "").toUpperCase();
  const stopped = Boolean(mission.emergency_stopped);
  const activeStep = steps.find((step) => !terminalStepStates.has(String(step.status || "").toUpperCase())) || steps.at(-1);

  missionStatusText.textContent = stopped ? "Interrompida por emergência" : formatMissionStatus(status);
  missionMeta.textContent = [id, mission.version ? `v${mission.version}` : ""].filter(Boolean).join(" · ") || "Missão consultada";
  missionObjective.textContent = mission.objective || "Objetivo não informado pelo runtime.";
  missionStep.textContent = describeStep(activeStep);
  missionEvidence.textContent = evidenceSummary(steps, events);
  statusClass(missionStatusDot, missionStateColor(status, stopped));
  emergencyStopButton.disabled = !id || stopped || ["COMPLETED", "FAILED", "CANCELLED"].includes(status);
}

function renderMissionLoading(id) {
  missionStatusText.textContent = "Consultando runtime…";
  missionMeta.textContent = id;
  missionObjective.textContent = "—";
  missionStep.textContent = "—";
  missionEvidence.textContent = "—";
  statusClass(missionStatusDot, "checking");
  emergencyStopButton.disabled = true;
}

function renderMissionError(id, message) {
  missionStatusText.textContent = "Não foi possível consultar";
  missionMeta.textContent = id || "Missão não informada";
  missionObjective.textContent = message;
  missionStep.textContent = "—";
  missionEvidence.textContent = "—";
  statusClass(missionStatusDot, "danger");
  emergencyStopButton.disabled = !id;
}

function persistMissionId(value) {
  const missionId = value.trim();
  missionIdInput.value = missionId;
  if (missionId) localStorage.setItem(missionKey, missionId);
  else localStorage.removeItem(missionKey);
  return missionId;
}

async function getMissionStatus(missionId, { announce = false } = {}) {
  const id = persistMissionId(missionId);
  if (!id) throw new Error("Informe o identificador da missão.");
  renderMissionLoading(id);
  try {
    const response = await fetchWithTimeout(`/api/missions/${encodeURIComponent(id)}`, {
      headers: authHeaders(),
      cache: "no-store",
    });
    const payload = await parseResponse(response);
    if (!response.ok) throw new Error(payload.detail || "Não foi possível consultar a missão.");
    renderMission(payload);
    if (announce) {
      const mission = normalizeMissionPayload(payload).mission;
      const text = `Missão ${mission.mission_id || id}: ${formatMissionStatus(mission.status)}. Parada de emergência: ${mission.emergency_stopped ? "sim" : "não"}.`;
      addMessage(text, "assistant");
      speak(text);
    }
    return payload;
  } catch (error) {
    renderMissionError(id, error.message);
    throw error;
  }
}

async function emergencyStop(missionId, reason = "Parada solicitada pelo usuário") {
  const id = persistMissionId(missionId);
  if (!id) throw new Error("Informe o identificador da missão.");
  const response = await fetchWithTimeout(`/api/missions/${encodeURIComponent(id)}/emergency-stop`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ actor: "Leandro", reason }),
  });
  const payload = await parseResponse(response);
  if (!response.ok) throw new Error(payload.detail || "Não foi possível parar a missão.");
  renderMission(payload);
  const text = `Parada de emergência registrada para ${payload.mission_id || id}.`;
  addMessage(text, "assistant");
  speak(text);
  return payload;
}

function captureMissionId(text) {
  const match = text.match(/\b(?:MCF|CHAT)-[A-Za-z0-9][A-Za-z0-9._-]{3,}\b/);
  if (!match) return;
  const id = persistMissionId(match[0]);
  if (localStorage.getItem(tokenKey)) getMissionStatus(id).catch(() => {});
}

async function sendMessage(message) {
  if (requestInFlight) return;
  requestInFlight = true;
  addMessage(message, "user");
  const pending = addMessage("Analisando solicitação…", "assistant", "pending");
  sendButton.disabled = true;
  input.disabled = true;
  if (micButton) micButton.disabled = true;

  try {
    const response = await fetchWithTimeout("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
    const payload = await parseResponse(response);
    if (!response.ok) throw new Error(payload.detail || "Não foi possível responder.");
    updateMessage(pending, payload.reply);
    captureMissionId(payload.reply);
    speak(payload.reply);
  } catch (error) {
    const messageText = error.name === "AbortError"
      ? "A resposta demorou mais de 30 segundos. Tente novamente em um minuto."
      : `Erro: ${error.message}`;
    updateMessage(pending, messageText, { error: true });
  } finally {
    requestInFlight = false;
    sendButton.disabled = false;
    input.disabled = false;
    if (micButton) micButton.disabled = false;
    input.focus();
  }
}

function setContextTab(tab) {
  const isMission = tab !== "system";
  missionPanel.hidden = !isMission;
  systemPanel.hidden = isMission;
  contextTitle.textContent = isMission ? "Missão" : "Sistema";
  document.querySelectorAll(".context-tab").forEach((button) => {
    const active = button.dataset.context === (isMission ? "mission" : "system");
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", active ? "true" : "false");
  });
}

function setActiveNav(view) {
  document.querySelectorAll(".nav-item").forEach((button) => {
    const active = button.dataset.view === view;
    button.classList.toggle("active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
}

function openContext(tab = "mission") {
  setContextTab(tab);
  setActiveNav(tab === "system" ? "system" : "mission");
  document.body.classList.add("context-open");
}

function closeContext() {
  document.body.classList.remove("context-open");
  setActiveNav("chat");
}

async function routeVoiceCommand(text) {
  const statusMatch = text.match(/^(?:status|situação) da missão\s+(.+)$/i);
  const stopMatch = text.match(/^(?:parar|pare a) missão\s+(.+)$/i);
  if (statusMatch) {
    const id = persistMissionId(statusMatch[1]);
    openContext("mission");
    await getMissionStatus(id, { announce: true });
    return;
  }
  if (stopMatch) {
    const id = persistMissionId(stopMatch[1]);
    openContext("mission");
    await emergencyStop(id, "Parada solicitada por comando de voz");
    return;
  }
  await sendMessage(text);
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

missionIdInput.addEventListener("change", () => persistMissionId(missionIdInput.value));

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => {
    const view = button.dataset.view;
    if (view === "chat") {
      closeContext();
      input.focus();
    } else {
      openContext(view);
      if (view === "system") checkHealth();
    }
  });
});

document.querySelectorAll(".context-tab").forEach((button) => {
  button.addEventListener("click", () => {
    setContextTab(button.dataset.context);
    setActiveNav(button.dataset.context === "system" ? "system" : "mission");
  });
});

document.querySelector("#mobileContextButton").addEventListener("click", () => openContext("mission"));
document.querySelector("#contextCloseButton").addEventListener("click", closeContext);
document.querySelector("#contextBackdrop").addEventListener("click", closeContext);

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && document.body.classList.contains("context-open") && !settingsDialog.open) closeContext();
});

document.querySelectorAll(".settings-trigger").forEach((button) => {
  button.addEventListener("click", () => {
    accessTokenInput.value = localStorage.getItem(tokenKey) || "";
    voiceOutputInput.checked = localStorage.getItem(voiceKey) === "1";
    if (!settingsDialog.open) settingsDialog.showModal();
  });
});

document.querySelector("#saveSettingsButton").addEventListener("click", () => {
  localStorage.setItem(tokenKey, accessTokenInput.value.trim());
  localStorage.setItem(voiceKey, voiceOutputInput.checked ? "1" : "0");
  checkHealth();
  const activeMission = missionIdInput.value.trim();
  if (activeMission) getMissionStatus(activeMission).catch(() => {});
});

document.querySelector("#newChatButton").addEventListener("click", async () => {
  try {
    await fetch(`/api/sessions/${encodeURIComponent(sessionId)}`, { method: "DELETE", headers: authHeaders() });
  } finally {
    sessionId = crypto.randomUUID();
    localStorage.setItem(sessionKey, sessionId);
    messages.replaceChildren();
    addMessage("Nova conversa iniciada. Qual é a missão?", "assistant");
    settingsDialog.close();
    input.focus();
  }
});

document.querySelector("#missionStatusButton").addEventListener("click", async () => {
  try {
    await getMissionStatus(missionIdInput.value.trim());
  } catch (error) {
    addMessage(`Erro ao consultar missão: ${error.message}`, "assistant", "error");
  }
});

document.querySelector("#refreshHealthButton").addEventListener("click", checkHealth);

emergencyStopButton.addEventListener("click", async () => {
  const missionId = missionIdInput.value.trim();
  if (!missionId || !window.confirm(`Parar imediatamente a missão ${missionId}?`)) return;
  emergencyStopButton.disabled = true;
  try {
    await emergencyStop(missionId);
  } catch (error) {
    addMessage(`Erro na parada de emergência: ${error.message}`, "assistant", "error");
    renderMissionError(missionId, error.message);
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
    setGlobalStatus("Ouvindo comando…", "warning");
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
      addMessage(`Erro: ${error.message}`, "assistant", "error");
    }
  });
  recognition.addEventListener("error", (event) => {
    if (event.error !== "no-speech") addMessage(`Não foi possível reconhecer a voz: ${event.error}.`, "assistant", "error");
  });
  micButton.addEventListener("click", () => {
    if (requestInFlight) return;
    try {
      recognition.start();
    } catch {
      // O navegador pode rejeitar chamadas duplicadas enquanto a captura anterior é encerrada.
    }
  });
}

if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js");

setContextTab("mission");
checkHealth();
const activeMission = missionIdInput.value.trim();
if (activeMission && localStorage.getItem(tokenKey)) getMissionStatus(activeMission).catch(() => {});
