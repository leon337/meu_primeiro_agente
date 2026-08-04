"""Cliente e validação do webhook da WhatsApp Cloud API."""

from collections import OrderedDict
import hashlib
import hmac
from threading import Lock
from typing import Any

import httpx


class MessageDeduplicator:
    """Memória limitada de IDs já aceitos no processo atual."""

    def __init__(self, max_entries: int = 2_000) -> None:
        if max_entries < 1:
            raise ValueError("max_entries deve ser positivo")
        self._max_entries = max_entries
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._lock = Lock()

    def claim(self, message_id: str) -> bool:
        """Retorna True apenas na primeira entrega conhecida do ID."""

        normalized = message_id.strip()
        if not normalized:
            return True
        with self._lock:
            if normalized in self._seen:
                self._seen.move_to_end(normalized)
                return False
            self._seen[normalized] = None
            while len(self._seen) > self._max_entries:
                self._seen.popitem(last=False)
            return True


def valid_signature(body: bytes, signature: str | None, app_secret: str) -> bool:
    if not app_secret or not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature.removeprefix("sha256="), expected)


def incoming_messages(payload: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Extrai (id, remetente, texto) das mensagens recebidas."""

    messages: list[tuple[str, str, str]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                text = message.get("text", {}).get("body")
                sender = message.get("from")
                message_id = message.get("id", "")
                if message.get("type") == "text" and sender and text:
                    messages.append((str(message_id), str(sender), str(text)))
    return messages


def incoming_texts(payload: dict[str, Any]) -> list[tuple[str, str]]:
    """Compatibilidade com consumidores que não precisam do ID da mensagem."""

    return [(sender, text) for _, sender, text in incoming_messages(payload)]


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
