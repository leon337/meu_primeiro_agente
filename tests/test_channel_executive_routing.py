from pathlib import Path

import pytest

from app.server import get_tool_registry
from app.tools.remote import RemoteToolRegistry


def test_chat_channels_receive_executive_tools_when_runtime_is_configured(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BRIDGE_URL", "https://bridge.example.com")
    monkeypatch.setenv("BRIDGE_DEVICE_TOKEN", "device-token")
    monkeypatch.setenv("AEP_CONTROL_TOKEN", "control-token")

    registry = get_tool_registry(tmp_path)

    assert isinstance(registry, RemoteToolRegistry)
    names = {item.name for item in registry.definitions}
    assert {
        "aep_submit_mission",
        "aep_get_mission",
        "aep_approve_step",
        "aep_emergency_stop",
    } <= names


def test_chat_channels_keep_diagnostic_tools_without_control_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BRIDGE_URL", "https://bridge.example.com")
    monkeypatch.setenv("BRIDGE_DEVICE_TOKEN", "device-token")
    monkeypatch.delenv("AEP_CONTROL_TOKEN", raising=False)

    registry = get_tool_registry(tmp_path)

    assert isinstance(registry, RemoteToolRegistry)
    assert {item.name for item in registry.definitions} == {
        "get_disk_space",
        "get_memory_usage",
        "get_system_info",
        "list_files",
    }
