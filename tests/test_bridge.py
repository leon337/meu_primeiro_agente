from pathlib import Path

import pytest
from fastapi import HTTPException

from app.bridge import ToolRequest, execute_tool, get_registry, require_device_token
from app.server import get_tool_registry
from app.tools.registry import ToolError
from app.tools.remote import EmptyToolRegistry, RemoteToolRegistry


def test_bridge_requires_device_token(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("BRIDGE_DEVICE_TOKEN", "token-seguro")
    with pytest.raises(HTTPException) as error:
        require_device_token("Bearer incorreto")
    assert error.value.status_code == 401
    assert require_device_token("Bearer token-seguro") is None


def test_bridge_executes_only_authorized_tool(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("ALLOWED_DIRECTORY", str(tmp_path))
    registry = get_registry()
    response = execute_tool(ToolRequest(name="get_disk_space"), registry)
    assert set(response["result"]) == {"total_gib", "used_gib", "free_gib", "percent_used"}

    with pytest.raises(HTTPException) as error:
        execute_tool(ToolRequest(name="exec", arguments={"command": "id"}), registry)
    assert error.value.status_code == 400


def test_remote_bridge_requires_https() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        RemoteToolRegistry("http://127.0.0.1:8787", "token")


def test_remote_bridge_executes_tool(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    class Response:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"result": {"free_gib": 10}}

    monkeypatch.setattr("app.tools.remote.httpx.post", lambda *args, **kwargs: Response())
    registry = RemoteToolRegistry("https://pc.example.com", "token")
    assert registry.execute("get_disk_space") == {"free_gib": 10}


def test_vercel_without_bridge_never_uses_cloud_machine(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("BRIDGE_URL", raising=False)
    monkeypatch.delenv("BRIDGE_DEVICE_TOKEN", raising=False)
    registry = get_tool_registry(tmp_path)
    assert isinstance(registry, EmptyToolRegistry)
    assert registry.definitions == []
    with pytest.raises(ToolError, match="Nenhum computador"):
        registry.execute("get_disk_space")
