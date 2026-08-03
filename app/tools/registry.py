"""Lista fechada e validada das únicas funções executáveis pelo agente."""

from collections.abc import Callable
from datetime import datetime
import logging
from pathlib import Path
from typing import Any

from app.models import ToolDefinition
from app.tools.disk import get_disk_space
from app.tools.files import list_files
from app.tools.memory import get_memory_usage
from app.tools.system import get_system_info

logger = logging.getLogger(__name__)


class ToolError(ValueError):
    pass


def tool_definitions() -> list[ToolDefinition]:
    empty = {"type": "object", "properties": {}, "additionalProperties": False}
    return [
        ToolDefinition("get_disk_space", "Consulta o espaço do disco no computador conectado.", empty),
        ToolDefinition("get_memory_usage", "Consulta a memória RAM no computador conectado.", empty),
        ToolDefinition("get_system_info", "Consulta sistema, arquitetura, nome e Python do computador conectado.", empty),
        ToolDefinition("list_files", "Lista nomes, tipos e tamanhos na pasta autorizada do computador conectado, sem ler conteúdo.", {"type": "object", "properties": {"path": {"type": "string", "description": "Caminho relativo à pasta autorizada; use '.' para a raiz."}}, "additionalProperties": False}),
    ]


class ToolRegistry:
    def __init__(self, allowed_directory: Path) -> None:
        self.allowed_directory = allowed_directory.resolve()
        self._handlers: dict[str, Callable[..., dict[str, Any]]] = {
            "get_disk_space": lambda: get_disk_space(self.allowed_directory),
            "get_memory_usage": get_memory_usage,
            "get_system_info": get_system_info,
            "list_files": lambda path=".": list_files(self.allowed_directory, path),
        }

    @property
    def definitions(self) -> list[ToolDefinition]:
        return tool_definitions()

    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = arguments or {}
        if name not in self._handlers:
            raise ToolError(f"Ferramenta não autorizada ou inexistente: {name}")
        if not isinstance(arguments, dict):
            raise ToolError("Os parâmetros devem ser um objeto")
        allowed = {"path"} if name == "list_files" else set()
        unexpected = set(arguments) - allowed
        if unexpected:
            raise ToolError("Parâmetros inválidos: " + ", ".join(sorted(unexpected)))
        print(f"[Solicitação {datetime.now().astimezone().isoformat(timespec='seconds')}: {name} | parâmetros: {arguments}]")
        logger.info("Executando ferramenta autorizada %s com parâmetros %s", name, arguments)
        try:
            return self._handlers[name](**arguments)
        except (TypeError, ValueError, OSError) as exc:
            raise ToolError(str(exc)) from exc
