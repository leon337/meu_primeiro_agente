"""Fábrica única para o runtime local do Agente Executivo Pessoal."""

from __future__ import annotations

import os
from pathlib import Path

from app.mcf.adapter import MCFAdapter
from app.missions.repository import SQLiteMissionRepository
from app.missions.service import MissionService
from app.policies.engine import PolicyEngine


def create_runtime(database_path: str | Path | None = None) -> tuple[MissionService, MCFAdapter]:
    configured = database_path or os.getenv("AEP_DATABASE_PATH", "var/aep/aep.sqlite3")
    repository = SQLiteMissionRepository(configured)
    service = MissionService(repository, PolicyEngine())
    adapter = MCFAdapter(service, os.getenv("AEP_AUDIT_SIGNING_KEY") or None)
    return service, adapter
