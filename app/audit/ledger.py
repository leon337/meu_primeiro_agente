"""Validação integral do encadeamento causal de eventos."""

from app.missions.events import compute_event_hash
from app.missions.models import MissionEvent


def validate_event_chain(events: list[MissionEvent]) -> bool:
    previous_hash = "0" * 64
    expected_sequence = 1
    for event in events:
        if event.sequence != expected_sequence or event.previous_hash != previous_hash:
            return False
        expected_hash = compute_event_hash(
            event.event_id,
            event.mission_id,
            event.event_type,
            event.sequence,
            event.payload,
            event.previous_hash,
            event.created_at,
        )
        if event.event_hash != expected_hash:
            return False
        previous_hash = event.event_hash
        expected_sequence += 1
    return True
