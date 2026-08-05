import pytest

from app.models import ProviderResponse
from app.providers.gemini_provider import GeminiProvider


def bare_provider() -> GeminiProvider:
    provider = GeminiProvider.__new__(GeminiProvider)
    provider._history = []  # type: ignore[attr-defined]
    return provider


def test_tool_result_is_sent_as_user_content() -> None:
    provider = bare_provider()
    provider._generate = lambda: ProviderResponse(text="ok")  # type: ignore[method-assign]

    response = provider.send_tool_results([("get_disk_space", {"output": {"free_gib": 1}})])

    assert response.text == "ok"
    assert provider._history[-1].role == "user"  # type: ignore[attr-defined]
    assert provider._history[-1].parts[0].function_response.name == "get_disk_space"  # type: ignore[attr-defined]


@pytest.mark.parametrize("method", ["message", "tool"])
def test_failed_request_does_not_contaminate_history(method: str) -> None:
    provider = bare_provider()

    def fail() -> ProviderResponse:
        raise RuntimeError("falha simulada")

    provider._generate = fail  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="falha simulada"):
        if method == "message":
            provider.send_message("olá")
        else:
            provider.send_tool_results([("get_memory_usage", {"output": {}})])
    assert provider._history == []  # type: ignore[attr-defined]


def test_provider_builds_unique_stable_model_chain() -> None:
    provider = GeminiProvider(
        api_key="fake-key",
        model_name="gemini-3.6-flash",
        tools=[],
        fallback_model_name="gemini-3.5-flash-lite",
    )

    assert provider._model_names == [  # type: ignore[attr-defined]
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite",
    ]


def test_request_timeout_is_never_below_gemini_minimum() -> None:
    provider = GeminiProvider(
        api_key="fake-key",
        model_name="gemini-3.6-flash",
        tools=[],
        request_timeout_ms=8_000,
    )

    assert provider._request_timeout_ms == 10_500  # type: ignore[attr-defined]


def test_tool_policy_requires_explicit_local_request() -> None:
    provider = GeminiProvider(
        api_key="fake-key",
        model_name="gemini-3.6-flash",
        tools=[],
    )

    instruction = str(provider._config.system_instruction)  # type: ignore[attr-defined]
    assert "somente quando o usuário pedir explicitamente" in instruction
    assert "identificadores de teste" in instruction
