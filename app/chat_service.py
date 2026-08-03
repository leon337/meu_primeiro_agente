"""Sessões isoladas do agente para os canais web e WhatsApp."""

from collections import OrderedDict
from pathlib import Path
from threading import RLock
from typing import Callable

from app.agent import Agent
from app.providers.gemini_provider import GeminiProvider
from app.tools.registry import ToolRegistry


class ChatService:
    """Mantém um conjunto limitado de agentes em memória por sessão."""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        allowed_directory: Path,
        fallback_model_name: str | None = None,
        max_sessions: int = 100,
        agent_factory: Callable[[], Agent] | None = None,
    ) -> None:
        self._api_key = api_key
        self._model_name = model_name
        self._fallback_model_name = fallback_model_name
        self._registry = ToolRegistry(allowed_directory)
        self._max_sessions = max_sessions
        self._agent_factory = agent_factory
        self._sessions: OrderedDict[str, Agent] = OrderedDict()
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

    def chat(self, session_id: str, message: str) -> str:
        session_id = session_id.strip()
        if not session_id or len(session_id) > 128:
            raise ValueError("Identificador de sessão inválido")
        with self._lock:
            agent = self._sessions.pop(session_id, None) or self._new_agent()
            self._sessions[session_id] = agent
            while len(self._sessions) > self._max_sessions:
                self._sessions.popitem(last=False)
            return agent.chat(message)

    def reset(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
