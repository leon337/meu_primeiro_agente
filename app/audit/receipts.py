"""Recibos canônicos opcionais, assinados sem expor o segredo."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def create_receipt(payload: dict[str, Any], signing_key: str | None = None) -> dict[str, Any]:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    receipt: dict[str, Any] = {"payload": payload, "sha256": digest, "signature": None}
    if signing_key:
        receipt["signature"] = hmac.new(signing_key.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    return receipt


def verify_receipt(receipt: dict[str, Any], signing_key: str | None = None) -> bool:
    payload = receipt.get("payload")
    if not isinstance(payload, dict):
        return False
    rebuilt = create_receipt(payload, signing_key)
    return hmac.compare_digest(str(receipt.get("sha256", "")), rebuilt["sha256"]) and (
        signing_key is None or hmac.compare_digest(str(receipt.get("signature", "")), str(rebuilt["signature"]))
    )
