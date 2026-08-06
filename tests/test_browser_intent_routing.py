from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest

from app.chat_service import ChatService
from app.models import ToolDefinition
from app.server import ChatRequest, answer_whatsapp, chat, health
from app.tools.registry import ToolError


class RecordingAgent:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def chat(self, message: str) -> str:
        self.messages.append(message)
        return f"IA: {message}"


class RecordingRegistry:
    def __init__(self, *, executive: bool = True, result: dict[str, Any] | None = None) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.result = result or {
            "mission_id": "CHAT-test-123",
            "status": "COMPLETED",
            "receipt": {"payload": {"status": "COMPLETED"}},
        }
        self._definitions = [
            ToolDefinition("get_disk_space", "diagnóstico", {"type": "object"}),
        ]
        if executive:
            self._definitions.append(
                ToolDefinition("aep_submit_mission", "missão", {"type": "object"})
            )

    @property
    def definitions(self) -> list[ToolDefinition]:
        return self._definitions

    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = arguments or {}
        self.calls.append((name, payload))
        return self.result


class FailingRegistry(RecordingRegistry):
    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append((name, arguments or {}))
        raise ToolError("token de controle inválido")


def make_service(
    tmp_path: Path,
    registry: RecordingRegistry,
    agent: RecordingAgent | None = None,
) -> tuple[ChatService, RecordingAgent]:
    fallback = agent or RecordingAgent()
    service = ChatService(
        "fake",
        "fake",
        tmp_path,
        registry=registry,
        agent_factory=lambda: fallback,  # type: ignore[arg-type,return-value]
    )
    return service, fallback


def submitted_steps(registry: RecordingRegistry) -> list[dict[str, Any]]:
    assert registry.calls and registry.calls[0][0] == "aep_submit_mission"
    return registry.calls[0][1]["steps"]


def test_capability_answer_is_grounded_in_registered_tool(tmp_path: Path) -> None:
    registry = RecordingRegistry(executive=True)
    service, agent = make_service(tmp_path, registry)

    reply = service.chat("web:capability", "Você consegue acessar sites?")

    assert "sim" in reply.lower()
    assert "computador conectado" in reply.lower()
    assert registry.calls == []
    assert agent.messages == []


def test_capability_answer_reports_runtime_unavailable(tmp_path: Path) -> None:
    registry = RecordingRegistry(executive=False)
    service, agent = make_service(tmp_path, registry)

    reply = service.chat("web:offline", "Você consegue navegar na internet?")

    assert "indisponível" in reply.lower()
    assert "runtime executivo" in reply.lower()
    assert registry.calls == []
    assert agent.messages == []


@pytest.mark.parametrize(
    ("message", "expected_action", "expected_target", "expected_application"),
    [
        ("Acesse https://example.com e leia o título principal da página.", "navigate", "https://example.com", None),
        ("Abra o Google", "navigate", "https://www.google.com/", None),
        ("Abra o Brave", "launch_application", "", "Brave"),
    ],
)
def test_explicit_browser_commands_create_deterministic_missions(
    tmp_path: Path,
    message: str,
    expected_action: str,
    expected_target: str,
    expected_application: str | None,
) -> None:
    registry = RecordingRegistry()
    service, agent = make_service(tmp_path, registry)

    reply = service.chat("web:command", message)

    steps = submitted_steps(registry)
    assert steps[0]["action"] == expected_action
    assert steps[0].get("target", "") == expected_target
    if expected_application:
        assert steps[0]["parameters"] == {"channel": "desktop", "application": expected_application}
    assert "CHAT-test-123" in reply
    assert "COMPLETED" in reply
    assert agent.messages == []


def test_research_request_navigates_and_extracts_text(tmp_path: Path) -> None:
    registry = RecordingRegistry()
    service, agent = make_service(tmp_path, registry)

    reply = service.chat(
        "whatsapp:research",
        "Pesquise na Wikipédia sobre inteligência artificial e me traga os primeiros resultados.",
    )

    steps = submitted_steps(registry)
    assert [step["action"] for step in steps] == ["navigate", "read_text"]
    assert steps[0]["target"].startswith("https://pt.wikipedia.org/w/index.php?search=")
    assert parse_qs(urlsplit(steps[0]["target"]).query)["search"] == ["inteligência artificial"]
    assert steps[1]["parameters"]["selector"] == "body"
    assert "CHAT-test-123" in reply
    assert agent.messages == []


def test_real_receipt_output_text_is_returned_to_the_user(tmp_path: Path) -> None:
    registry = RecordingRegistry(
        result={
            "mission_id": "CHAT-real-schema",
            "status": "COMPLETED",
            "receipt": {
                "payload": {
                    "steps": [
                        {
                            "evidence": [
                                {
                                    "data": {
                                        "outputs": [
                                            {"url": "https://example.com/"},
                                            {"text": "Example Domain"},
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                }
            },
        }
    )
    service, _ = make_service(tmp_path, registry)

    reply = service.chat("web:real-receipt", "Acesse https://example.com e leia o título.")

    assert "Resultado verificado" in reply
    assert "Example Domain" in reply


def test_conceptual_question_stays_with_ai_and_does_not_open_browser(tmp_path: Path) -> None:
    registry = RecordingRegistry()
    service, agent = make_service(tmp_path, registry)

    reply = service.chat("web:concept", "Explique o que é inteligência artificial")

    assert reply == "IA: Explique o que é inteligência artificial"
    assert registry.calls == []
    assert agent.messages == ["Explique o que é inteligência artificial"]


def test_runtime_or_invalid_token_failure_is_reported_without_false_success(tmp_path: Path) -> None:
    registry = FailingRegistry()
    service, agent = make_service(tmp_path, registry)

    reply = service.chat("web:bad-token", "Abra o Google")

    assert "não foi possível" in reply.lower()
    assert "runtime executivo" in reply.lower()
    assert "conclu" not in reply.lower()
    assert "token" not in reply.lower()
    assert agent.messages == []


def test_web_endpoint_uses_the_same_deterministic_route(tmp_path: Path) -> None:
    registry = RecordingRegistry()
    service, _ = make_service(tmp_path, registry)

    response = chat(ChatRequest(message="Abra o Google", session_id="web-endpoint"), service)

    assert response.reply.startswith("Missão CHAT-test-123")
    assert submitted_steps(registry)[0]["target"] == "https://www.google.com/"


def test_whatsapp_answer_uses_the_same_deterministic_route(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = RecordingRegistry()
    service, _ = make_service(tmp_path, registry)
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr("app.server.get_chat_service", lambda: service)
    monkeypatch.setattr(
        "app.server.send_text",
        lambda sender, reply, *_args: sent.append((sender, reply)),
    )
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "not-recorded")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "not-recorded")

    answer_whatsapp("5581999999999", "Abra o Google")

    assert sent[0][0] == "5581999999999"
    assert sent[0][1].startswith("Missão CHAT-test-123")
    assert submitted_steps(registry)[0]["target"] == "https://www.google.com/"


def test_health_does_not_claim_executive_capability_for_legacy_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class LegacyRemoteRegistry(RecordingRegistry):
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            super().__init__(executive=False)

        def health(self) -> bool:
            return True

    monkeypatch.setenv("BRIDGE_URL", "https://bridge.example.com")
    monkeypatch.setenv("BRIDGE_DEVICE_TOKEN", "device-token")
    monkeypatch.setenv("AEP_CONTROL_TOKEN", "control-token")
    monkeypatch.setattr("app.server.RemoteToolRegistry", LegacyRemoteRegistry)

    payload = health()

    assert payload["bridge_connected"] is True
    assert payload["executive_configured"] is False
