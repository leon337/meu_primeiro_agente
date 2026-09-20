from __future__ import annotations

import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app import server
from app.whatsapp_audit import WhatsAppAuditClient


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


class FakeAudit:
    def __init__(self) -> None:
        self.messages = []
        self.events = []

    def record_message(self, *args, **kwargs):
        self.messages.append((args, kwargs))

    def record_event(self, *args, **kwargs):
        self.events.append((args, kwargs))


def test_audit_client_is_noop_when_not_configured(monkeypatch) -> None:
    monkeypatch.setattr("app.whatsapp_audit.httpx.post", lambda *a, **k: (_ for _ in ()).throw(AssertionError()))
    client = WhatsAppAuditClient("", "", "")
    assert client.record_message("5581000000000", "mid", "inbound", "oi", "received") is None


def test_audit_client_calls_protected_rpc(monkeypatch) -> None:
    seen = {}

    def fake_post(url, **kwargs):
        seen["url"] = url
        seen["json"] = kwargs["json"]
        return FakeResponse("message-id")

    monkeypatch.setattr("app.whatsapp_audit.httpx.post", fake_post)
    client = WhatsAppAuditClient("https://example.supabase.co", "pub", "audit-secret", "model-x")
    assert client.record_message("5581000000000", "mid", "inbound", "oi", "received") == "message-id"
    assert seen["url"].endswith("/rest/v1/rpc/audit_whatsapp_message")
    assert seen["json"]["p_audit_token"] == "audit-secret"
    assert seen["json"]["p_model_name"] is None


def test_answer_whatsapp_audits_outbound(monkeypatch) -> None:
    audit = FakeAudit()

    class FakeBakery:
        def chat(self, sender: str, message: str) -> str:
            return "Resposta da padaria"

    monkeypatch.setattr(server, "get_whatsapp_audit", lambda: audit)
    monkeypatch.setattr(server, "get_bakery_chat_service", lambda: FakeBakery())
    monkeypatch.setattr(server, "send_text", lambda *a, **k: {"messages": [{"id": "wamid.out"}]})
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "token")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "phone-id")
    server.answer_whatsapp("5581000000000", "Olá", "wamid.in")
    assert any(args[2] == "outbound" and args[4] == "sent" for args, _ in audit.messages)
    assert any(kwargs.get("meta_message_id") == "wamid.out" for _, kwargs in audit.events)


def test_webhook_audits_inbound(monkeypatch) -> None:
    audit = FakeAudit()
    monkeypatch.setattr(server, "get_whatsapp_audit", lambda: audit)
    monkeypatch.setattr(server, "answer_whatsapp", lambda *a, **k: None)
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "secret")
    payload = {
        "entry": [{"changes": [{"value": {"messages": [{
            "id": "wamid.unique.audit",
            "from": "5581000000000",
            "type": "text",
            "text": {"body": "Boa noite"},
        }]}}]}]
    }
    raw = json.dumps(payload).encode()
    signature = "sha256=" + hmac.new(b"secret", raw, hashlib.sha256).hexdigest()
    with TestClient(server.app) as client:
        response = client.post(
            "/api/whatsapp/webhook",
            content=raw,
            headers={"x-hub-signature-256": signature, "content-type": "application/json"},
        )
    assert response.status_code == 200
    assert response.json()["accepted"] == "1"
    assert any(args[2] == "inbound" and args[3] == "Boa noite" for args, _ in audit.messages)
