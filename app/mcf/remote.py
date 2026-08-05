"""Cliente HTTPS da API de controle do runtime local."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

import httpx


class RemoteMissionError(RuntimeError):
    pass


class RemoteMissionClient:
    def __init__(self, bridge_url: str, control_token: str, timeout: float = 20.0) -> None:
        parsed = urlsplit(bridge_url.strip())
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("BRIDGE_URL deve ser HTTPS")
        if not control_token.strip():
            raise ValueError("AEP_CONTROL_TOKEN não configurado")
        self.base_url = bridge_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {control_token.strip()}"}
        self.timeout = timeout

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = httpx.request(
                method,
                self.base_url + path,
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RemoteMissionError("O runtime executivo local não respondeu") from exc
        if not isinstance(data, dict):
            raise RemoteMissionError("Resposta inválida do runtime executivo")
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

    def approve(self, mission_id: str, step_id: str, approved: bool, actor: str, reason: str = "") -> dict[str, Any]:
        return self._request(
            "POST",
            f"/missions/{mission_id}/steps/{step_id}/approval",
            {"approved": approved, "actor": actor, "reason": reason},
        )

    def emergency_stop(self, mission_id: str, actor: str, reason: str) -> dict[str, Any]:
        return self._request("POST", f"/missions/{mission_id}/emergency-stop", {"actor": actor, "reason": reason})
