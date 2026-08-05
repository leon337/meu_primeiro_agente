"""Eventos auditáveis com encadeamento causal por hash."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import uuid4

from app.missions.models import MissionEvent, utc_now


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def compute_event_hash(
    event_id: str,
    mission_id: str,
    event_type: str,
    sequence: int,
    payload: dict[str, Any],
    previous_hash: str,
    created_at: str,
) -> str:
    material = canonical_json(
        {
            "event_id": event_id,
            "mission_id": mission_id,
            "event_type": event_type,
            "sequence": sequence,
            "payload": payload,
            "previous_hash": previous_hash,
            "created_at": created_at,
        }
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def build_event(
    mission_id: str,
    event_type: str,
    sequence: int,
    payload: dict[str, Any],
    previous_hash: str,
) -> MissionEvent:
    created_at = utc_now()
    event_id = str(uuid4())
    event_hash = compute_event_hash(
        event_id, mission_id, event_type, sequence, payload, previous_hash, created_at
    )
    return MissionEvent(event_id, mission_id, event_type, sequence, payload, previous_hash, event_hash, created_at)
