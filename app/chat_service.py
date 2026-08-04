"""Sessões isoladas do agente para os canais web e WhatsApp."""

from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock
from typing import Callable

from app.agent import Agent
from app.providers.gemini_provider import GeminiProvider
from app.tools.base import ToolExecutor
from app.tools.registry import ToolRegistry


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

    def chat(self, session_id: str, message: str) -> str:
        session_id = self._validate_session_id(session_id)
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
