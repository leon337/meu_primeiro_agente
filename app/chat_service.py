"""Sessões isoladas do agente para os canais web e WhatsApp."""

from collections import OrderedDict
from dataclasses import dataclass, field
from hashlib import sha256
import json
import logging
from pathlib import Path
from threading import RLock
from typing import Callable

from app.agent import Agent
from app.browser_routing import BrowserRoute, route_browser_intent
from app.providers.gemini_provider import GeminiProvider
from app.tools.base import ToolExecutor
from app.tools.registry import ToolRegistry


logger = logging.getLogger(__name__)


@dataclass
class _SessionState:
    """Estado e fila exclusiva de uma sessão."""

    agent: Agent
    lock: RLock = field(default_factory=RLock)
    active_requests: int = 0


class ChatService:
    """Mantém agentes isolados e serializa apenas mensagens da mesma sessão."""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        allowed_directory: Path,
        fallback_model_name: str | None = None,
        registry: ToolExecutor | None = None,
        max_sessions: int = 100,
        agent_factory: Callable[[], Agent] | None = None,
    ) -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._fallback_model_name = fallback_model_name
        self._registry = registry or ToolRegistry(allowed_directory)
        self._max_sessions = max_sessions
        self._agent_factory = agent_factory
        self._sessions: OrderedDict[str, _SessionState] = OrderedDict()
        self._lock = RLock()

    def _new_agent(self) -> Agent:
        if self._agent_factory is not None:
            return self._agent_factory()
        provider = GeminiProvider(
            self._api_key,
            self._model_name,
            self._registry.definitions,
            self._fallback_model_name,
        )
        return Agent(provider, self._registry)

    @staticmethod
    def _validate_session_id(session_id: str) -> str:
        normalized = session_id.strip()
        if not normalized or len(normalized) > 128:
            raise ValueError("Identificador de sessão inválido")
        return normalized

    def _evict_idle_sessions(self) -> None:
        """Mantém o limite sem remover sessões que estão executando ou aguardando."""

        if len(self._sessions) <= self._max_sessions:
            return
        for candidate_id, state in list(self._sessions.items()):
            if len(self._sessions) <= self._max_sessions:
                break
            if state.active_requests == 0:
                self._sessions.pop(candidate_id, None)

    def _executive_available(self) -> bool:
        return any(definition.name == "aep_submit_mission" for definition in self._registry.definitions)

    @staticmethod
    def _channel(session_id: str) -> str:
        return session_id.split(":", 1)[0] if ":" in session_id else "web"

    @staticmethod
    def _session_reference(session_id: str) -> str:
        return sha256(session_id.encode("utf-8")).hexdigest()[:12]

    def _log_route(self, session_id: str, route: str, available: bool, mission_id: str = "") -> None:
        logger.info(
            "chat_route %s",
            json.dumps(
                {
                    "channel": self._channel(session_id),
                    "session_ref": self._session_reference(session_id),
                    "route": route,
                    "executive_available": available,
                    "mission_id": mission_id,
                },
                ensure_ascii=True,
                sort_keys=True,
            ),
        )

    @staticmethod
    def _evidence_text(result: dict[str, object]) -> str:
        receipt = result.get("receipt")
        if not isinstance(receipt, dict):
            return ""
        payload = receipt.get("payload")
        if not isinstance(payload, dict):
            return ""
        steps = payload.get("steps")
        if not isinstance(steps, list):
            return ""
        texts: list[str] = []
        for step in steps:
            if not isinstance(step, dict):
                continue
            evidence = step.get("evidence")
            if not isinstance(evidence, list):
                continue
            for item in evidence:
                if not isinstance(item, dict) or not isinstance(item.get("data"), dict):
                    continue
                data = item["data"]
                value = data.get("text")
                if isinstance(value, str) and value.strip():
                    texts.append(value.strip())
                outputs = data.get("outputs")
                if not isinstance(outputs, list):
                    continue
                for output in outputs:
                    if not isinstance(output, dict):
                        continue
                    output_text = output.get("text")
                    if isinstance(output_text, str) and output_text.strip():
                        texts.append(output_text.strip())
        return "\n\n".join(texts)[-4000:]

    def _handle_browser_route(self, session_id: str, route: BrowserRoute) -> str | None:
        if route.kind == "fallback":
            return None
        available = self._executive_available()
        if route.kind == "capability":
            self._log_route(session_id, route.kind, available)
            if available:
                return (
                    "Sim. Posso acessar sites pelo navegador do computador conectado, "
                    "criando uma missão auditável quando você pedir uma ação explícita."
                )
            return (
                "O recurso de navegação está indisponível nesta sessão porque o runtime executivo "
                "do computador conectado não está disponível."
            )
        if not available or route.mission is None:
            self._log_route(session_id, route.kind, available)
            return (
                "Não foi possível executar a navegação: o runtime executivo do computador conectado "
                "está indisponível nesta sessão."
            )
        try:
            result = self._registry.execute("aep_submit_mission", route.mission)
        except Exception:
            # A exceção remota pode conter detalhes do provedor. Não a registre:
            # o evento estruturado abaixo é suficiente para operação sem risco de segredo.
            self._log_route(session_id, "browser_action_failed", available)
            return (
                "Não foi possível encaminhar a ação ao runtime executivo do computador conectado. "
                "Confirme a conexão e tente novamente."
            )
        mission_id = str(result.get("mission_id", "não informado"))
        mission_status = str(result.get("status", "UNKNOWN"))
        self._log_route(session_id, route.kind, available, mission_id)
        reply = f"Missão {mission_id} criada. Estado: {mission_status}."
        evidence = self._evidence_text(result)
        if evidence:
            reply += f"\n\nResultado verificado:\n{evidence}"
        elif mission_status not in {"COMPLETED", "FAILED", "BLOCKED", "CANCELLED", "WAITING_HUMAN"}:
            reply += " A execução continua no runtime local e pode ser consultada pelo identificador da missão."
        return reply

    def chat(self, session_id: str, message: str) -> str:
        session_id = self._validate_session_id(session_id)
        if not message.strip():
            raise ValueError("A mensagem não pode estar vazia")
        route = route_browser_intent(message)
        routed_reply = self._handle_browser_route(session_id, route)
        if routed_reply is not None:
            return routed_reply
        self._log_route(session_id, "ai_fallback", self._executive_available())
        with self._lock:
            state = self._sessions.pop(session_id, None)
            if state is None:
                state = _SessionState(self._new_agent())
            state.active_requests += 1
            self._sessions[session_id] = state
            self._evict_idle_sessions()

        try:
            # Conversas iguais permanecem ordenadas; sessões diferentes não se bloqueiam.
            with state.lock:
                return state.agent.chat(message)
        finally:
            with self._lock:
                state.active_requests -= 1
                if self._sessions.get(session_id) is state:
                    self._sessions.move_to_end(session_id)
                self._evict_idle_sessions()

    def reset(self, session_id: str) -> None:
        session_id = self._validate_session_id(session_id)
        with self._lock:
            state = self._sessions.get(session_id)
            if state is None:
                return
            state.active_requests += 1

        try:
            with state.lock:
                with self._lock:
                    if self._sessions.get(session_id) is state:
                        self._sessions.pop(session_id, None)
        finally:
            with self._lock:
                state.active_requests -= 1
