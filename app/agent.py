"""Orquestrador independente do Gemini e das implementações de ferramentas."""

from typing import Any

from app.models import ProviderResponse
from app.providers.base import AIProvider
from app.tools.registry import ToolRegistry


class Agent:
    def __init__(self, provider: AIProvider, registry: ToolRegistry, max_tool_rounds: int = 5) -> None:
        self.provider = provider
        self.registry = registry
        self.max_tool_rounds = max_tool_rounds

    def chat(self, message: str) -> str:
        if not message.strip():
            raise ValueError("A mensagem não pode estar vazia")
        response = self.provider.send_message(message)
        for _ in range(self.max_tool_rounds):
            if not response.tool_calls:
                return response.text or "Não recebi uma resposta em texto do modelo."
            results: list[tuple[str, dict[str, Any]]] = []
            for call in response.tool_calls:
                print(f"[Agente solicitou: {call.name}]")
                print("[Executando ferramenta autorizada...]")
                try:
                    result = {"output": self.registry.execute(call.name, call.arguments)}
                except Exception as exc:  # erro controlado volta ao modelo, sem interromper a conversa
                    result = {"error": str(exc)}
                results.append((call.name, result))
            response = self.provider.send_tool_results(results)
        raise RuntimeError("Limite de rodadas de ferramentas atingido")

