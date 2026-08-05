"""Normalização mínima de comandos de voz antes do chat ou runtime."""

from dataclasses import dataclass
from enum import StrEnum


class VoiceIntent(StrEnum):
    CHAT = "CHAT"
    STATUS = "STATUS"
    STOP = "STOP"
    APPROVE = "APPROVE"
    REJECT = "REJECT"


@dataclass(frozen=True, slots=True)
class ParsedVoiceCommand:
    intent: VoiceIntent
    text: str
    mission_id: str = ""


def parse_voice_command(text: str) -> ParsedVoiceCommand:
    normalized = " ".join(text.strip().split())
    lowered = normalized.casefold()
    if lowered.startswith(("parar missão ", "pare a missão ")):
        return ParsedVoiceCommand(VoiceIntent.STOP, normalized, normalized.rsplit(" ", 1)[-1])
    if lowered.startswith(("status da missão ", "situação da missão ")):
        return ParsedVoiceCommand(VoiceIntent.STATUS, normalized, normalized.rsplit(" ", 1)[-1])
    if lowered.startswith(("aprovar missão ", "aprove a missão ")):
        return ParsedVoiceCommand(VoiceIntent.APPROVE, normalized, normalized.rsplit(" ", 1)[-1])
    if lowered.startswith(("rejeitar missão ", "rejeite a missão ")):
        return ParsedVoiceCommand(VoiceIntent.REJECT, normalized, normalized.rsplit(" ", 1)[-1])
    return ParsedVoiceCommand(VoiceIntent.CHAT, normalized)
