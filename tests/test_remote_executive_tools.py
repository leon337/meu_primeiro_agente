from __future__ import annotations

from typing import Any

import pytest

from app.tools.registry import ToolError
from app.tools.remote import RemoteToolRegistry


class FakeMissionClient:
    def __init__(self, mission_status: str = "COMPLETED") -> None:
        self.calls: list[tuple[str, Any]] = []
        self.mission_status = mission_status

    def create_mission(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(("create", payload))
        return {"mission_id": payload["mission_id"], "status": "CREATED", "version": 1}

    def transition(self, mission_id: str, target: str, expected_version: int | None = None) -> dict[str, Any]:
        self.calls.append(("transition", mission_id, target, expected_version))
        version = 2 if target == "PLANNING" else 3
        return {"mission_id": mission_id, "status": target, "version": version}

    def add_step(self, mission_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(("step", mission_id, payload))
        return {
            "step_id": f"step-{payload['sequence']}",
            "status": "PENDING",
            "requires_approval": False,
            "risk": "LOW",
        }

    def get_mission(self, mission_id: str) -> dict[str, Any]:
        self.calls.append(("get", mission_id))
        return {
            "mission_id": mission_id,
            "status": self.mission_status,
            "receipt": {"payload": {"mission_id": mission_id, "status": self.mission_status}},
        }

    def approve(
        self,
        mission_id: str,
        step_id: str,
        approved: bool,
        actor: str,
        reason: str = "",
    ) -> dict[str, Any]:
        self.calls.append(("approve", mission_id, step_id, approved, actor, reason))
        return {"approval_id": "approval-1", "status": "APPROVED" if approved else "REJECTED"}

    def emergency_stop(self, mission_id: str, actor: str, reason: str) -> dict[str, Any]:
        self.calls.append(("stop", mission_id, actor, reason))
        return {"mission_id": mission_id, "status": "CANCELLED", "emergency_stopped": True}


def make_registry(client: FakeMissionClient | None = None) -> RemoteToolRegistry:
    return RemoteToolRegistry(
        "https://bridge.example.com",
        "device-token",
        mission_client=client,
    )


def test_executive_tools_are_exposed_only_with_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AEP_CONTROL_TOKEN", raising=False)
    without_runtime = make_registry()
    assert {item.name for item in without_runtime.definitions} == {
        "get_disk_space",
        "get_memory_usage",
        "get_system_info",
        "list_files",
    }

    with_runtime = make_registry(FakeMissionClient())
    names = {item.name for item in with_runtime.definitions}
    assert {
        "aep_submit_mission",
        "aep_get_mission",
        "aep_approve_step",
        "aep_emergency_stop",
    } <= names


def test_submit_mission_creates_plans_and_releases_runtime() -> None:
    client = FakeMissionClient()
    registry = make_registry(client)

    result = registry.execute(
        "aep_submit_mission",
        {
            "objective": "Abrir o painel e ler o título",
            "steps": [
                {
                    "action": "navigate",
                    "capability": "observe",
                    "target": "https://vercel.com/dashboard",
                    "parameters": {"channel": "browser"},
                },
                {
                    "action": "read_text",
                    "capability": "observe",
                    "target": "https://vercel.com/dashboard",
                    "parameters": {"channel": "browser", "selector": "h1"},
                },
            ],
            "completion_criteria": ["título devolvido com evidência"],
            "max_autonomy": 3,
            "wait_seconds": 0,
        },
    )

    assert result["status"] == "READY"
    assert str(result["mission_id"]).startswith("CHAT-")
    assert [call[0] for call in client.calls] == ["create", "transition", "step", "step", "transition"]

    created_payload = client.calls[0][1]
    assert created_payload["allowed_domains"] == ["vercel.com"]
    assert created_payload["allowed_capabilities"] == ["observe"]
    assert created_payload["requester_agent"] == "ChatService"
    assert created_payload["return_to"] == "chat"
    assert created_payload["owner_authorized"] is True
    assert "token" not in str(created_payload).lower()

    assert client.calls[1][2:] == ("PLANNING", 1)
    assert client.calls[-1][2:] == ("READY", 2)


def test_submit_mission_waits_for_terminal_receipt() -> None:
    client = FakeMissionClient("COMPLETED")
    registry = make_registry(client)

    result = registry.execute(
        "aep_submit_mission",
        {
            "objective": "Abrir o site",
            "steps": [
                {
                    "action": "navigate",
                    "capability": "observe",
                    "target": "https://example.com",
                    "parameters": {"channel": "browser"},
                }
            ],
            "wait_seconds": 1,
        },
    )

    assert result["status"] == "COMPLETED"
    assert result["receipt"]["payload"]["status"] == "COMPLETED"
    assert [call[0] for call in client.calls][-1] == "get"
    assert client.calls[0][1]["max_autonomy"] == 4


def test_submit_mission_rejects_insecure_or_invalid_payloads() -> None:
    registry = make_registry(FakeMissionClient())

    with pytest.raises(ToolError, match="HTTPS"):
        registry.execute(
            "aep_submit_mission",
            {
                "objective": "Abrir site inseguro",
                "steps": [
                    {
                        "action": "navigate",
                        "capability": "observe",
                        "target": "http://example.com",
                    }
                ],
            },
        )

    with pytest.raises(ToolError, match="Parâmetros inválidos"):
        registry.execute(
            "aep_submit_mission",
            {
                "objective": "Teste",
                "steps": [{"action": "navigate", "capability": "observe"}],
                "password": "nao-deve-entrar",
            },
        )

    with pytest.raises(ToolError, match="1 a 20"):
        registry.execute("aep_submit_mission", {"objective": "Teste", "steps": []})

    with pytest.raises(ToolError, match="0 e 15"):
        registry.execute(
            "aep_submit_mission",
            {
                "objective": "Teste",
                "steps": [{"action": "navigate", "capability": "observe"}],
                "wait_seconds": 16,
            },
        )


def test_status_approval_and_emergency_are_forwarded() -> None:
    client = FakeMissionClient()
    registry = make_registry(client)

    assert registry.execute("aep_get_mission", {"mission_id": "MCF-1"})["status"] == "COMPLETED"
    assert registry.execute(
        "aep_approve_step",
        {"mission_id": "MCF-1", "step_id": "STEP-1", "approved": True, "reason": "Autorizado"},
    )["status"] == "APPROVED"
    assert registry.execute(
        "aep_emergency_stop",
        {"mission_id": "MCF-1", "reason": "Interromper agora"},
    )["status"] == "CANCELLED"

    assert client.calls == [
        ("get", "MCF-1"),
        ("approve", "MCF-1", "STEP-1", True, "Leandro", "Autorizado"),
        ("stop", "MCF-1", "Leandro", "Interromper agora"),
    ]


def test_executive_tool_requires_configured_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AEP_CONTROL_TOKEN", raising=False)
    registry = make_registry()
    with pytest.raises(ToolError, match="Runtime executivo"):
        registry.execute("aep_get_mission", {"mission_id": "MCF-1"})
