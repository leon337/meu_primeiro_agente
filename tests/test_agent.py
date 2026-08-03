from pathlib import Path
from typing import Any

from app.agent import Agent
from app.models import ProviderResponse, ToolCall
from app.providers.base import AIProvider
from app.tools.registry import ToolRegistry


class FakeProvider(AIProvider):
    def __init__(self) -> None:
        self.results: list[tuple[str, dict[str, Any]]] = []

    def send_message(self, message: str) -> ProviderResponse:
        return ProviderResponse(tool_calls=[ToolCall("get_system_info")])

    def send_tool_results(self, results: list[tuple[str, dict[str, Any]]]) -> ProviderResponse:
        self.results = results
        return ProviderResponse(text="Resposta final em português.")


def test_agent_tool_cycle_without_real_api(tmp_path: Path) -> None:
    provider = FakeProvider()
    answer = Agent(provider, ToolRegistry(tmp_path)).chat("Qual é meu sistema?")
    assert answer == "Resposta final em português."
    assert provider.results[0][0] == "get_system_info"
    assert "output" in provider.results[0][1]

