"""Executor das ferramentas através da ponte HTTPS instalada no computador."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

import httpx

from app.mcf.remote import RemoteMissionClient
from app.models import ToolDefinition
from app.tools.registry import ToolError, tool_definitions


_EXECUTIVE_TOOL_NAMES = {
    "aep_submit_mission",
    "aep_get_mission",
    "aep_approve_step",
    "aep_emergency_stop",
}


def executive_tool_definitions() -> list[ToolDefinition]:
    """Ferramentas de alto nível expostas ao modelo sem revelar tokens ou segredos."""

    step_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": (
                    "Ação declarativa. Navegador: navigate, read_text, click, fill, "
                    "fill_credential, select, screenshot, download ou submit. Desktop: "
                    "focus_application, click_named_control, set_named_text ou read_named_text."
                ),
            },
            "capability": {
                "type": "string",
                "description": (
                    "Classe de capacidade: observe, prepare, execute_reversible, communicate, "
                    "publish, install ou delete."
                ),
            },
            "target": {
                "type": "string",
                "description": "URL HTTPS para navegador; deixe vazio para ação de desktop.",
            },
            "parameters": {
                "type": "object",
                "description": (
                    "Parâmetros da ação. Use channel=browser com selector/value/credential_ref/options; "
                    "ou channel=desktop com application/control_name/value."
                ),
                "additionalProperties": True,
            },
        },
        "required": ["action", "capability"],
        "additionalProperties": False,
    }
    return [
        ToolDefinition(
            "aep_submit_mission",
            (
                "Cria e libera uma missão no runtime executivo local quando o usuário pedir explicitamente "
                "uma ação no navegador ou no computador. Retorna o identificador para acompanhamento."
            ),
            {
                "type": "object",
                "properties": {
                    "objective": {"type": "string", "description": "Objetivo concreto solicitado pelo usuário."},
                    "steps": {
                        "type": "array",
                        "items": step_schema,
                        "minItems": 1,
                        "maxItems": 20,
                    },
                    "allowed_domains": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Domínios autorizados; quando omitido, são derivados das URLs das etapas.",
                    },
                    "completion_criteria": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Critérios objetivos de conclusão.",
                    },
                    "forbidden_actions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Ações declarativas que esta missão não poderá executar.",
                    },
                    "max_autonomy": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Nível máximo de autonomia da missão; padrão 3.",
                    },
                },
                "required": ["objective", "steps"],
                "additionalProperties": False,
            },
        ),
        ToolDefinition(
            "aep_get_mission",
            "Consulta estado, etapas, erros e recibo auditável de uma missão executiva.",
            {
                "type": "object",
                "properties": {"mission_id": {"type": "string"}},
                "required": ["mission_id"],
                "additionalProperties": False,
            },
        ),
        ToolDefinition(
            "aep_approve_step",
            "Aprova ou rejeita uma etapa que está aguardando decisão humana.",
            {
                "type": "object",
                "properties": {
                    "mission_id": {"type": "string"},
                    "step_id": {"type": "string"},
                    "approved": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
                "required": ["mission_id", "step_id", "approved"],
                "additionalProperties": False,
            },
        ),
        ToolDefinition(
            "aep_emergency_stop",
            "Interrompe imediatamente uma missão, impedindo novas ações e preservando as evidências.",
            {
                "type": "object",
                "properties": {
                    "mission_id": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["mission_id"],
                "additionalProperties": False,
            },
        ),
    ]


class EmptyToolRegistry:
    @property
    def definitions(self) -> list[ToolDefinition]:
        return []

    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        raise ToolError("Nenhum computador está conectado")


class RemoteToolRegistry:
    def __init__(
        self,
        bridge_url: str,
        device_token: str,
        timeout: float = 20.0,
        control_token: str | None = None,
        mission_client: Any | None = None,
    ) -> None:
        self.bridge_url = self._validate_url(bridge_url)
        if not device_token.strip():
            raise ValueError("BRIDGE_DEVICE_TOKEN não configurado")
        self.device_token = device_token.strip()
        self.timeout = timeout
        self._mission_client = mission_client
        effective_control_token = control_token if control_token is not None else os.getenv("AEP_CONTROL_TOKEN", "")
        if self._mission_client is None and effective_control_token.strip():
            self._mission_client = RemoteMissionClient(
                self.bridge_url,
                effective_control_token.strip(),
                timeout=timeout,
            )

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
        definitions = tool_definitions()
        if self._mission_client is not None:
            definitions.extend(executive_tool_definitions())
        return definitions

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
        if name in _EXECUTIVE_TOOL_NAMES:
            return self._execute_executive(name, arguments or {})
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

    def _execute_executive(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self._mission_client is None:
            raise ToolError("Runtime executivo não configurado")
        if not isinstance(arguments, dict):
            raise ToolError("Os parâmetros devem ser um objeto")
        if name == "aep_submit_mission":
            return self._submit_mission(arguments)
        if name == "aep_get_mission":
            mission_id = self._required_text(arguments, "mission_id")
            self._reject_unexpected(arguments, {"mission_id"})
            return self._mission_client.get_mission(mission_id)
        if name == "aep_approve_step":
            self._reject_unexpected(arguments, {"mission_id", "step_id", "approved", "reason"})
            mission_id = self._required_text(arguments, "mission_id")
            step_id = self._required_text(arguments, "step_id")
            approved = arguments.get("approved")
            if not isinstance(approved, bool):
                raise ToolError("approved deve ser booleano")
            return self._mission_client.approve(
                mission_id,
                step_id,
                approved,
                "Leandro",
                str(arguments.get("reason", ""))[:500],
            )
        if name == "aep_emergency_stop":
            self._reject_unexpected(arguments, {"mission_id", "reason"})
            mission_id = self._required_text(arguments, "mission_id")
            reason = str(arguments.get("reason", "Parada solicitada pelo proprietário"))[:500]
            return self._mission_client.emergency_stop(mission_id, "Leandro", reason)
        raise ToolError(f"Ferramenta executiva desconhecida: {name}")

    def _submit_mission(self, arguments: dict[str, Any]) -> dict[str, Any]:
        self._reject_unexpected(
            arguments,
            {"objective", "steps", "allowed_domains", "completion_criteria", "forbidden_actions", "max_autonomy"},
        )
        objective = self._required_text(arguments, "objective")
        raw_steps = arguments.get("steps")
        if not isinstance(raw_steps, list) or not 1 <= len(raw_steps) <= 20:
            raise ToolError("steps deve conter de 1 a 20 etapas")

        steps: list[dict[str, Any]] = []
        derived_domains: set[str] = set()
        derived_capabilities: set[str] = set()
        for sequence, raw_step in enumerate(raw_steps, start=1):
            if not isinstance(raw_step, dict):
                raise ToolError("Cada etapa deve ser um objeto")
            self._reject_unexpected(raw_step, {"action", "capability", "target", "parameters"})
            action = self._required_text(raw_step, "action")
            capability = self._required_text(raw_step, "capability")
            target = str(raw_step.get("target", "")).strip()
            parameters = raw_step.get("parameters", {})
            if not isinstance(parameters, dict):
                raise ToolError("parameters deve ser um objeto")
            if target:
                parsed = urlsplit(target)
                if parsed.scheme or parsed.hostname:
                    if parsed.scheme != "https" or not parsed.hostname:
                        raise ToolError("Destinos web devem usar URL HTTPS completa")
                    derived_domains.add(parsed.hostname.lower())
            derived_capabilities.add(capability)
            steps.append(
                {
                    "sequence": sequence,
                    "action": action,
                    "capability": capability,
                    "target": target,
                    "parameters": parameters,
                }
            )

        configured_domains = arguments.get("allowed_domains", [])
        if not isinstance(configured_domains, list):
            raise ToolError("allowed_domains deve ser uma lista")
        domains = sorted(
            {str(item).strip().lower() for item in configured_domains if str(item).strip()} | derived_domains
        )
        criteria = arguments.get("completion_criteria", ["todas as etapas concluídas com evidência"])
        if not isinstance(criteria, list) or not criteria:
            raise ToolError("completion_criteria deve ser uma lista não vazia")
        forbidden = arguments.get("forbidden_actions", [])
        if not isinstance(forbidden, list):
            raise ToolError("forbidden_actions deve ser uma lista")
        max_autonomy = arguments.get("max_autonomy", 3)
        if not isinstance(max_autonomy, int) or not 1 <= max_autonomy <= 5:
            raise ToolError("max_autonomy deve estar entre 1 e 5")

        mission_id = f"CHAT-{uuid4()}"
        created = self._mission_client.create_mission(
            {
                "mission_id": mission_id,
                "requester_agent": "ChatService",
                "objective": objective,
                "return_to": "chat",
                "allowed_domains": domains,
                "allowed_capabilities": sorted(derived_capabilities),
                "forbidden_actions": [str(item) for item in forbidden],
                "completion_criteria": [str(item) for item in criteria],
                "max_autonomy": max_autonomy,
            }
        )
        planning = self._mission_client.transition(mission_id, "PLANNING", created.get("version"))
        planned_steps = [self._mission_client.add_step(mission_id, step) for step in steps]
        ready = self._mission_client.transition(mission_id, "READY", planning.get("version"))
        return {
            "mission_id": mission_id,
            "status": ready.get("status", "READY"),
            "version": ready.get("version"),
            "planned_steps": planned_steps,
            "message": "Missão enviada ao runtime local para execução e auditoria.",
        }

    @staticmethod
    def _required_text(arguments: dict[str, Any], key: str) -> str:
        value = arguments.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ToolError(f"{key} é obrigatório")
        return value.strip()

    @staticmethod
    def _reject_unexpected(arguments: dict[str, Any], allowed: set[str]) -> None:
        unexpected = set(arguments) - allowed
        if unexpected:
            raise ToolError("Parâmetros inválidos: " + ", ".join(sorted(unexpected)))
