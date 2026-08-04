import hashlib
import hmac
import json
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.agent import Agent
from app.chat_service import ChatService
from app.models import ProviderResponse
from app.providers.base import AIProvider
from app.server import (
    ChatRequest,
    chat,
    data_deletion,
    home,
    privacy_policy,
    require_app_token,
    reset_session,
    terms_of_service,
)
from app.whatsapp import incoming_texts, valid_signature


class EchoProvider(AIProvider):
    def send_message(self, message: str) -> ProviderResponse:
        return ProviderResponse(text=f"Eco: {message}")

    def send_tool_results(self, results):  # type: ignore[no-untyped-def]
        return ProviderResponse(text="resultado")


def fake_service(tmp_path: Path) -> ChatService:
    return ChatService("fake", "fake", tmp_path, agent_factory=lambda: Agent(EchoProvider(), None))  # type: ignore[arg-type]


def test_chat_and_reset_routes(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("APP_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    service = fake_service(tmp_path)
    response = chat(ChatRequest(message="olá", session_id="teste"), service)
    assert response.reply == "Eco: olá"
    assert reset_session("teste", service) is None


def test_app_token_is_required_when_configured(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("APP_ACCESS_TOKEN", "segredo")
    with pytest.raises(HTTPException) as error:
        require_app_token(None)
    assert error.value.status_code == 401
    assert require_app_token("Bearer segredo") is None


def test_whatsapp_signature_and_message_parsing() -> None:
    body = b'{"object":"whatsapp_business_account"}'
    signature = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    assert valid_signature(body, signature, "secret")
    assert not valid_signature(body + b"x", signature, "secret")

    payload = json.loads(
        '{"entry":[{"changes":[{"value":{"messages":['
        '{"from":"5581999999999","type":"text","text":{"body":"Olá"}}]}}]}]}'
    )
    assert incoming_texts(payload) == [("5581999999999", "Olá")]


def test_pwa_home_is_available() -> None:
    response = home()
    assert Path(response.path).name == "index.html"
    assert "Hello Agent" in Path(response.path).read_text(encoding="utf-8")


def test_public_compliance_pages_are_available_without_filesystem() -> None:
    pages = (
        (privacy_policy(), "Política de Privacidade"),
        (data_deletion(), "Exclusão de Dados"),
        (terms_of_service(), "Termos de Serviço"),
    )
    for response, expected_text in pages:
        body = response.body.decode("utf-8")
        assert response.status_code == 200
        assert response.media_type == "text/html"
        assert expected_text.lower() in body.lower()
        assert "eiasophia25@gmail.com" in body
