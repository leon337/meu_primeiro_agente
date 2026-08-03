"""Contrato comum para ferramentas locais e remotas."""

from typing import Any, Protocol

from app.models import ToolDefinition


class ToolExecutor(Protocol):
    @property
    def definitions(self) -> list[ToolDefinition]: ...

    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]: ...
