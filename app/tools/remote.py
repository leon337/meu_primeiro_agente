"""Executor das ferramentas através da ponte HTTPS instalada no computador."""

from typing import Any
from urllib.parse import urlsplit

import httpx

from app.models import ToolDefinition
from app.tools.registry import ToolError, tool_definitions


class EmptyToolRegistry:
    @property
    def definitions(self) -> list[ToolDefinition]:
        return []

    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        raise ToolError("Nenhum computador está conectado")


class RemoteToolRegistry:
    def __init__(self, bridge_url: str, device_token: str, timeout: float = 20.0) -> None:
        self.bridge_url = self._validate_url(bridge_url)
        if not device_token.strip():
            raise ValueError("BRIDGE_DEVICE_TOKEN não configurado")
        self.device_token = device_token.strip()
        self.timeout = timeout

    @staticmethod
    def _validate_url(value: str) -> str:
        parsed = urlsplit(value.strip())
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("BRIDGE_URL deve ser uma URL HTTPS pública")
        if parsed.query or parsed.fragment:
            raise ValueError("BRIDGE_URL não pode conter query ou fragmento")
        return value.strip().rstrip("/")

    @property
    def definitions(self) -> list[ToolDefinition]:
        return tool_definitions()

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.device_token}"}

    def health(self) -> bool:
        try:
            response = httpx.get(f"{self.bridge_url}/health", headers=self.headers, timeout=5)
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self.bridge_url}/tools/execute",
                headers=self.headers,
                json={"name": name, "arguments": arguments or {}},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ToolError("O computador conectado não respondeu à ferramenta") from exc
        result = payload.get("result")
        if not isinstance(result, dict):
            raise ToolError("A ponte local retornou uma resposta inválida")
        return result
