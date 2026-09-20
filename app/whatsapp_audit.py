"""Persistência best-effort e protegida da auditoria WhatsApp da Pão Nosso."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class WhatsAppAuditClient:
    """Escreve no ledger da Pão Nosso sem expor segredos e sem quebrar o atendimento."""

    def __init__(
        self,
        supabase_url: str,
        publishable_key: str,
        audit_token: str,
        model_name: str | None = None,
    ) -> None:
        self._url = supabase_url.rstrip("/")
        self._key = publishable_key.strip()
        self._token = audit_token.strip()
        self._model_name = (model_name or "").strip() or None

    @property
    def enabled(self) -> bool:
        return bool(self._url and self._key and self._token)
    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        }

    def _rpc(self, name: str, payload: dict[str, Any]) -> Any | None:
        if not self.enabled:
            return None
        try:
            response = httpx.post(
                f"{self._url}/rest/v1/rpc/{name}",
                headers=self._headers(),
                json={"p_audit_token": self._token, **payload},
                timeout=8,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            logger.exception("Falha best-effort na auditoria WhatsApp: %s", name)
            return None

    def record_message(
        self,
        customer_phone: str,
        meta_message_id: str | None,
        direction: str,
        body: str,
        status: str,
        *,
        model_name: str | None = None,
        order_code: str | None = None,
    ) -> Any | None:
        return self._rpc(
            "audit_whatsapp_message",
            {
                "p_customer_phone": customer_phone,
                "p_meta_message_id": meta_message_id,
                "p_direction": direction,
                "p_body": body[:4096],
                "p_status": status,
                "p_model_name": model_name,
                "p_order_code": order_code,
            },
        )

    def record_event(
        self,
        customer_phone: str,
        event_type: str,
        *,
        meta_message_id: str | None = None,
        tool_name: str | None = None,
        order_code: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> Any | None:
        return self._rpc(
            "audit_whatsapp_event",
            {
                "p_customer_phone": customer_phone,
                "p_event_type": event_type,
                "p_meta_message_id": meta_message_id,
                "p_tool_name": tool_name,
                "p_order_code": order_code,
                "p_detail": detail or {},
            },
        )
