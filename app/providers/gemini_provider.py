"""Adaptador Gemini. Nenhuma outra camada conhece tipos do SDK Google."""

from threading import Lock
from time import monotonic
from typing import Any

from google import genai
from google.genai import types

from app.models import ProviderResponse, ToolCall, ToolDefinition
from app.providers.base import AIProvider, tool_definitions_to_dicts


class GeminiProvider(AIProvider):
    """Cliente Gemini com timeout, failover e resfriamento por modelo."""

    _cooldown_lock = Lock()
    _cooldown_until: dict[str, float] = {}
    _stable_fallbacks = (
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite",
    )

    def __init__(
        self,
        api_key: str,
        model_name: str,
        tools: list[ToolDefinition],
        fallback_model_name: str | None = None,
        request_timeout_ms: int = 8_000,
        cooldown_seconds: float = 60.0,
    ) -> None:
        retry_options = types.HttpRetryOptions(
            attempts=1,
            initial_delay=0.5,
            max_delay=1.0,
            exp_base=2.0,
            jitter=0.5,
            http_status_codes=[408, 429, 500, 502, 503, 504],
        )
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=request_timeout_ms,
                retry_options=retry_options,
            ),
        )
        self._model_names = list(
            dict.fromkeys(
                filter(
                    None,
                    (model_name, fallback_model_name, *self._stable_fallbacks),
                )
            )
        )
        self._cooldown_seconds = cooldown_seconds
        declarations = [types.FunctionDeclaration(**item) for item in tool_definitions_to_dicts(tools)]
        self._config = types.GenerateContentConfig(
            system_instruction=(
                "Você é um assistente didático. Responda sempre em português. "
                "Use somente as ferramentas declaradas e nunca invente resultados. "
                "Não peça nem exponha chaves, segredos ou conteúdo de arquivos. "
                "Acione uma ferramenta somente quando o usuário pedir explicitamente "
                "uma informação ou ação local compatível. Não acione ferramentas para "
                "saudações, conversa casual, identificadores de teste ou mensagens ambíguas."
            ),
            tools=[types.Tool(function_declarations=declarations)] if declarations else None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        self._history: list[types.Content] = []

    @staticmethod
    def _is_transient_error(exc: Exception) -> bool:
        status_code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        text = f"{status_code} {exc}".lower()
        return any(marker in text for marker in ("408", "429", "500", "502", "503", "504", "timeout", "timed out"))

    @classmethod
    def _is_in_cooldown(cls, model_name: str) -> bool:
        with cls._cooldown_lock:
            expires_at = cls._cooldown_until.get(model_name, 0.0)
            if expires_at <= monotonic():
                cls._cooldown_until.pop(model_name, None)
                return False
            return True

    @classmethod
    def _mark_cooldown(cls, model_name: str, seconds: float) -> None:
        with cls._cooldown_lock:
            cls._cooldown_until[model_name] = max(
                cls._cooldown_until.get(model_name, 0.0),
                monotonic() + seconds,
            )

    @classmethod
    def _clear_cooldown(cls, model_name: str) -> None:
        with cls._cooldown_lock:
            cls._cooldown_until.pop(model_name, None)

    def _generate(self) -> ProviderResponse:
        response = None
        last_error: Exception | None = None
        attempted = False

        for model_name in self._model_names:
            if self._is_in_cooldown(model_name):
                continue
            attempted = True
            try:
                response = self._client.models.generate_content(
                    model=model_name,
                    contents=self._history,
                    config=self._config,
                )
                self._clear_cooldown(model_name)
                break
            except Exception as exc:
                last_error = exc
                if not self._is_transient_error(exc):
                    raise
                self._mark_cooldown(model_name, self._cooldown_seconds)

        if response is None:
            if not attempted:
                raise RuntimeError(
                    "Os modelos de IA estão temporariamente limitados. Aguarde um minuto e tente novamente."
                )
            raise RuntimeError(
                "Os modelos Gemini estão temporariamente indisponíveis. Tente novamente em instantes."
            ) from last_error
        if not response.candidates or response.candidates[0].content is None:
            raise RuntimeError("O Gemini não retornou uma resposta utilizável")
        model_content = response.candidates[0].content
        self._history.append(model_content)
        calls = [ToolCall(call.name or "", dict(call.args or {})) for call in (response.function_calls or [])]
        text_parts = [part.text for part in (model_content.parts or []) if part.text]
        return ProviderResponse("\n".join(text_parts).strip(), calls)

    def send_message(self, message: str) -> ProviderResponse:
        self._history.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))
        try:
            return self._generate()
        except Exception:
            self._history.pop()
            raise

    def send_tool_results(self, results: list[tuple[str, dict[str, Any]]]) -> ProviderResponse:
        parts = [types.Part.from_function_response(name=name, response=result) for name, result in results]
        self._history.append(types.Content(role="user", parts=parts))
        try:
            return self._generate()
        except Exception:
            self._history.pop()
            raise
