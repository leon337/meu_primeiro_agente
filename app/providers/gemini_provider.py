"""Adaptador Gemini. Nenhuma outra camada conhece tipos do SDK Google."""

from typing import Any

from google import genai
from google.genai import types

from app.models import ProviderResponse, ToolCall, ToolDefinition
from app.providers.base import AIProvider, tool_definitions_to_dicts


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model_name: str, tools: list[ToolDefinition]) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name
        declarations = [types.FunctionDeclaration(**item) for item in tool_definitions_to_dicts(tools)]
        self._config = types.GenerateContentConfig(
            system_instruction=("Você é um assistente didático. Responda sempre em português. "
                                "Use somente as ferramentas declaradas e nunca invente resultados. "
                                "Não peça nem exponha chaves, segredos ou conteúdo de arquivos."),
            tools=[types.Tool(function_declarations=declarations)],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        self._history: list[types.Content] = []

    def _generate(self) -> ProviderResponse:
        response = self._client.models.generate_content(model=self._model_name, contents=self._history, config=self._config)
        if not response.candidates or response.candidates[0].content is None:
            raise RuntimeError("O Gemini não retornou uma resposta utilizável")
        model_content = response.candidates[0].content
        self._history.append(model_content)
        calls = [ToolCall(call.name or "", dict(call.args or {})) for call in (response.function_calls or [])]
        text_parts = [part.text for part in (model_content.parts or []) if part.text]
        return ProviderResponse("\n".join(text_parts).strip(), calls)

    def send_message(self, message: str) -> ProviderResponse:
        self._history.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))
        return self._generate()

    def send_tool_results(self, results: list[tuple[str, dict[str, Any]]]) -> ProviderResponse:
        parts = [types.Part.from_function_response(name=name, response=result) for name, result in results]
        self._history.append(types.Content(role="tool", parts=parts))
        return self._generate()

