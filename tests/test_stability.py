from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Lock
from time import sleep
from types import SimpleNamespace

import pytest

from app.chat_service import ChatService
from app.providers.gemini_provider import GeminiProvider
from app.whatsapp import MessageDeduplicator


class ParallelAgent:
    def __init__(self, barrier: Barrier) -> None:
        self._barrier = barrier

    def chat(self, message: str) -> str:
        self._barrier.wait(timeout=2)
        return message


class SerialAgent:
    def __init__(self) -> None:
        self._guard = Lock()
        self.active = 0
        self.max_active = 0

    def chat(self, message: str) -> str:
        with self._guard:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        sleep(0.05)
        with self._guard:
            self.active -= 1
        return message


def test_different_sessions_do_not_block_each_other(tmp_path: Path) -> None:
    barrier = Barrier(2)
    service = ChatService(
        "fake",
        "fake",
        tmp_path,
        agent_factory=lambda: ParallelAgent(barrier),  # type: ignore[arg-type,return-value]
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(service.chat, "web", "web-ok")
        second = executor.submit(service.chat, "whatsapp", "whatsapp-ok")
        assert {first.result(timeout=3), second.result(timeout=3)} == {"web-ok", "whatsapp-ok"}


def test_same_session_is_processed_sequentially(tmp_path: Path) -> None:
    agent = SerialAgent()
    service = ChatService(
        "fake",
        "fake",
        tmp_path,
        agent_factory=lambda: agent,  # type: ignore[arg-type,return-value]
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(service.chat, "same", "one")
        second = executor.submit(service.chat, "same", "two")
        assert {first.result(timeout=3), second.result(timeout=3)} == {"one", "two"}
    assert agent.max_active == 1


class TooManyRequests(Exception):
    code = 429


class FakeModels:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def generate_content(self, *, model, contents, config):  # type: ignore[no-untyped-def]
        self.calls.append(model)
        if model == "primary":
            raise TooManyRequests("429 quota")
        content = SimpleNamespace(parts=[SimpleNamespace(text="fallback-ok")])
        return SimpleNamespace(
            candidates=[SimpleNamespace(content=content)],
            function_calls=[],
        )


def test_rate_limited_model_enters_cooldown_and_fallback_is_used() -> None:
    GeminiProvider._clear_cooldown("primary")
    GeminiProvider._clear_cooldown("fallback")
    provider = GeminiProvider.__new__(GeminiProvider)
    models = FakeModels()
    provider._client = SimpleNamespace(models=models)  # type: ignore[attr-defined]
    provider._model_names = ["primary", "fallback"]  # type: ignore[attr-defined]
    provider._cooldown_seconds = 60.0  # type: ignore[attr-defined]
    provider._history = []  # type: ignore[attr-defined]
    provider._config = None  # type: ignore[attr-defined]

    first = provider._generate()
    second = provider._generate()

    assert first.text == "fallback-ok"
    assert second.text == "fallback-ok"
    assert models.calls == ["primary", "fallback", "fallback"]
    GeminiProvider._clear_cooldown("primary")
    GeminiProvider._clear_cooldown("fallback")


def test_message_deduplicator_accepts_only_first_delivery() -> None:
    deduplicator = MessageDeduplicator(max_entries=2)
    assert deduplicator.claim("wamid.1")
    assert not deduplicator.claim("wamid.1")
    assert deduplicator.claim("wamid.2")
    assert deduplicator.claim("wamid.3")
    assert deduplicator.claim("wamid.1")  # saiu da janela limitada


def test_web_client_has_timeout_and_always_clears_pending_state() -> None:
    source = Path("public/app.js").read_text(encoding="utf-8")
    assert "AbortController" in source
    assert "requestTimeoutMs = 30000" in source
    assert 'pending.classList.remove("pending")' in source
