from abc import ABC, abstractmethod
from typing import Any

from app.models import ProviderResponse, ToolDefinition


class AIProvider(ABC):
    @abstractmethod
    def send_message(self, message: str) -> ProviderResponse:
        """Envia uma fala do usuário."""

    @abstractmethod
    def send_tool_results(self, results: list[tuple[str, dict[str, Any]]]) -> ProviderResponse:
        """Devolve resultados de ferramentas solicitadas pelo modelo."""


def tool_definitions_to_dicts(definitions: list[ToolDefinition]) -> list[dict[str, Any]]:
    return [{"name": item.name, "description": item.description, "parameters_json_schema": item.parameters} for item in definitions]

