#!/usr/bin/env python3
"""Gate local real: ferramenta do chat -> bridge -> daemon -> Playwright -> recibo."""

from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx

from app.tools.remote import RemoteToolRegistry


TERMINAL_STATES = {"COMPLETED", "FAILED", "BLOCKED", "CANCELLED", "WAITING_HUMAN"}


class LocalMissionClient:
    """Cliente do gate para a bridge HTTP isolada; produção continua exigindo HTTPS."""

    def __init__(self, base_url: str, token: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}"}
        self.timeout = timeout

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        response = httpx.request(
            method,
            self.base_url + path,
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("Bridge retornou resposta não estruturada")
        return data

    def create_mission(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/missions", payload)

    def get_mission(self, mission_id: str) -> dict[str, Any]:
        return self._request("GET", f"/missions/{mission_id}")

    def transition(self, mission_id: str, target: str, expected_version: int | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"target": target}
        if expected_version is not None:
            payload["expected_version"] = expected_version
        return self._request("POST", f"/missions/{mission_id}/transition", payload)

    def add_step(self, mission_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", f"/missions/{mission_id}/steps", payload)

    def approve(
        self,
        mission_id: str,
        step_id: str,
        approved: bool,
        actor: str,
        reason: str = "",
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/missions/{mission_id}/steps/{step_id}/approval",
            {"approved": approved, "actor": actor, "reason": reason},
        )

    def emergency_stop(self, mission_id: str, actor: str, reason: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/missions/{mission_id}/emergency-stop",
            {"actor": actor, "reason": reason},
        )


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _stop(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _tail(path: Path, max_lines: int = 40) -> str:
    if not path.exists():
        return ""
    return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:])


def _wait_for_bridge(base_url: str, device_token: str, bridge: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 20
    headers = {"Authorization": f"Bearer {device_token}"}
    while time.monotonic() < deadline:
        if bridge.poll() is not None:
            raise RuntimeError("Bridge temporária encerrou antes do health check")
        try:
            response = httpx.get(base_url + "/health", headers=headers, timeout=1.5)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.25)
    raise RuntimeError("Bridge temporária não ficou pronta em 20 segundos")


def _extract_text(result: dict[str, Any]) -> str:
    receipt = result.get("receipt")
    if not isinstance(receipt, dict):
        return ""
    payload = receipt.get("payload")
    if not isinstance(payload, dict):
        return ""
    for step in payload.get("steps", []):
        if not isinstance(step, dict):
            continue
        for evidence in step.get("evidence", []):
            if not isinstance(evidence, dict):
                continue
            data = evidence.get("data")
            if not isinstance(data, dict):
                continue
            for output in data.get("outputs", []):
                if isinstance(output, dict) and isinstance(output.get("text"), str):
                    return output["text"]
    return ""


def main() -> int:
    root = ROOT
    if Path.cwd().resolve() != root:
        os.chdir(root)

    with tempfile.TemporaryDirectory(prefix="aep-chat-routing-") as temporary:
        work = Path(temporary)
        port = _free_port()
        base_url = f"http://127.0.0.1:{port}"
        control_token = secrets.token_urlsafe(32)
        device_token = secrets.token_urlsafe(32)
        environment = os.environ.copy()
        environment.update(
            {
                "PYTHONUNBUFFERED": "1",
                "AEP_CONTROL_TOKEN": control_token,
                "BRIDGE_DEVICE_TOKEN": device_token,
                "AEP_AUDIT_SIGNING_KEY": secrets.token_urlsafe(32),
                "AEP_DATABASE_PATH": str(work / "aep.sqlite3"),
                "AEP_BROWSER_REAL": "1",
                "AEP_BROWSER_HEADLESS": "1",
                "AEP_BROWSER_PROFILE": str(work / "browser-profile"),
                "AEP_DESKTOP_REAL": "0",
                "AEP_DESKTOP_APPS": "Brave,Visual Studio Code",
                "ALLOWED_DIRECTORY": str(root),
            }
        )
        bridge_log = work / "bridge.log"
        daemon_log = work / "daemon.log"
        bridge: subprocess.Popen[bytes] | None = None
        daemon: subprocess.Popen[bytes] | None = None
        try:
            with bridge_log.open("wb") as bridge_stream, daemon_log.open("wb") as daemon_stream:
                bridge = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "app.bridge:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(port),
                        "--log-level",
                        "warning",
                    ],
                    cwd=root,
                    env=environment,
                    stdout=bridge_stream,
                    stderr=subprocess.STDOUT,
                )
                _wait_for_bridge(base_url, device_token, bridge)
                daemon = subprocess.Popen(
                    [sys.executable, "-m", "app.runtime.daemon"],
                    cwd=root,
                    env=environment,
                    stdout=daemon_stream,
                    stderr=subprocess.STDOUT,
                )

                client = LocalMissionClient(base_url, control_token)
                registry = RemoteToolRegistry(
                    "https://local-gate.invalid",
                    device_token,
                    mission_client=client,
                )
                result = registry.execute(
                    "aep_submit_mission",
                    {
                        "objective": "Ler o título público de example.com e devolver evidência",
                        "steps": [
                            {
                                "action": "read_text",
                                "capability": "observe",
                                "target": "https://example.com/",
                                "parameters": {"channel": "browser", "selector": "h1"},
                            }
                        ],
                        "completion_criteria": ["texto Example Domain presente no recibo"],
                        "max_autonomy": 4,
                        "wait_seconds": 15,
                    },
                )

            status = str(result.get("status", ""))
            text = _extract_text(result)
            receipt = result.get("receipt")
            payload = receipt.get("payload", {}) if isinstance(receipt, dict) else {}
            checks = {
                "mission_terminal": status in TERMINAL_STATES,
                "mission_completed": status == "COMPLETED",
                "owner_authorized": isinstance(payload, dict) and payload.get("owner_authorized") is True,
                "receipt_present": isinstance(receipt, dict) and bool(receipt.get("sha256")),
                "evidence_text_verified": "Example Domain" in text,
            }
            output = {
                "gate": "AEP_CHAT_ROUTING_LOCAL",
                "mission_id": result.get("mission_id"),
                "status": status,
                "checks": checks,
                "result": "PASS" if all(checks.values()) else "FAIL",
            }
            print(json.dumps(output, ensure_ascii=False, sort_keys=True))
            return 0 if output["result"] == "PASS" else 1
        except Exception as exc:
            print(
                json.dumps(
                    {
                        "gate": "AEP_CHAT_ROUTING_LOCAL",
                        "result": "ERROR",
                        "error": str(exc)[:500],
                        "bridge_log_tail": _tail(bridge_log),
                        "daemon_log_tail": _tail(daemon_log),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
            return 1
        finally:
            _stop(daemon)
            _stop(bridge)


if __name__ == "__main__":
    raise SystemExit(main())
