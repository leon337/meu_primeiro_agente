"""Memória operacional separada da conversa e sem segredos."""

from __future__ import annotations

from typing import Any

from app.missions.repository import SQLiteMissionRepository


class OperationalMemory:
    def __init__(self, repository: SQLiteMissionRepository) -> None:
        self.repository = repository

    def remember(self, namespace: str, key: str, value: dict[str, Any], sensitivity: str = "INTERNAL") -> None:
        if namespace not in {"mission", "preference", "resource", "checkpoint"}:
            raise ValueError("Namespace de memória não permitido")
        self.repository.put_memory(f"{namespace}:{key}", value, sensitivity)

    def recall(self, namespace: str, key: str) -> dict[str, Any] | None:
        return self.repository.get_memory(f"{namespace}:{key}")
