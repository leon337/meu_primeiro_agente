"""Cliente e validação do webhook da WhatsApp Cloud API."""

import hashlib
import hmac
from typing import Any

import httpx


def valid_signature(body: bytes, signature: str | None, app_secret: str) -> bool:
    if not app_secret or not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature.removeprefix("sha256="), expected)


def incoming_texts(payload: dict[str, Any]) -> list[tuple[str, str]]:
    messages: list[tuple[str, str]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                text = message.get("text", {}).get("body")
                sender = message.get("from")
                if message.get("type") == "text" and sender and text:
                    messages.append((str(sender), str(text)))
    return messages


def send_text(
    recipient: str,
    text: str,
    access_token: str,
    phone_number_id: str,
    graph_version: str,
) -> None:
    url = f"https://graph.facebook.com/{graph_version}/{phone_number_id}/messages"
    response = httpx.post(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"body": text[:4096]},
        },
        timeout=20,
    )
    response.raise_for_status()
