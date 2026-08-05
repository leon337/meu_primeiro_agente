"""Persistência SQLite transacional e substituível do runtime de missões."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from threading import RLock
from typing import Any, Protocol

from app.missions.events import build_event
from app.missions.models import (
    Approval,
    ApprovalStatus,
    AutonomyLevel,
    Mission,
    MissionEvent,
    MissionStatus,
    MissionStep,
    RiskLevel,
    StepStatus,
    utc_now,
)


class MissionNotFound(KeyError):
    pass


class ConcurrentUpdate(RuntimeError):
    pass


class MissionRepository(Protocol):
    def create_mission(self, mission: Mission) -> Mission: ...
    def get_mission(self, mission_id: str) -> Mission: ...
    def update_mission(self, mission: Mission, expected_version: int) -> Mission: ...
    def add_step(self, step: MissionStep) -> MissionStep: ...
    def list_steps(self, mission_id: str) -> list[MissionStep]: ...
    def append_event(self, mission_id: str, event_type: str, payload: dict[str, Any]) -> MissionEvent: ...


class SQLiteMissionRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        self._lock = RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def _initialize(self) -> None:
        if self.database_path != ":memory:":
            Path(self.database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );
                INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (1, CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS missions (
                    mission_id TEXT PRIMARY KEY,
                    requester TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    return_to TEXT NOT NULL,
                    allowed_domains TEXT NOT NULL,
                    allowed_capabilities TEXT NOT NULL,
                    forbidden_actions TEXT NOT NULL,
                    completion_criteria TEXT NOT NULL,
                    max_autonomy INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    emergency_stopped INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS mission_steps (
                    step_id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL REFERENCES missions(mission_id) ON DELETE CASCADE,
                    sequence INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    target TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    risk TEXT NOT NULL,
                    requires_approval INTEGER NOT NULL,
                    approval_status TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    version INTEGER NOT NULL,
                    evidence TEXT NOT NULL,
                    sanitized_error TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(mission_id, sequence)
                );
                CREATE TABLE IF NOT EXISTS mission_events (
                    event_id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL REFERENCES missions(mission_id) ON DELETE CASCADE,
                    sequence INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(mission_id, sequence)
                );
                CREATE TABLE IF NOT EXISTS approvals (
                    approval_id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL REFERENCES missions(mission_id) ON DELETE CASCADE,
                    step_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    requested_by TEXT NOT NULL,
                    decided_by TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    decided_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS operational_memory (
                    memory_key TEXT PRIMARY KEY,
                    memory_value TEXT NOT NULL,
                    sensitivity TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)

    def create_mission(self, mission: Mission) -> Mission:
        with self._lock, self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """INSERT INTO missions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        mission.mission_id,
                        mission.requester,
                        mission.objective,
                        mission.return_to,
                        self._json(mission.allowed_domains),
                        self._json(mission.allowed_capabilities),
                        self._json(mission.forbidden_actions),
                        self._json(mission.completion_criteria),
                        int(mission.max_autonomy),
                        mission.status.value,
                        mission.version,
                        int(mission.emergency_stopped),
                        mission.created_at,
                        mission.updated_at,
                        self._json(mission.metadata),
                    ),
                )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        self.append_event(mission.mission_id, "MISSION_CREATED", {"status": mission.status.value})
        return mission

    def get_mission(self, mission_id: str) -> Mission:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM missions WHERE mission_id = ?", (mission_id,)).fetchone()
        if row is None:
            raise MissionNotFound(mission_id)
        return Mission(
            mission_id=row["mission_id"],
            requester=row["requester"],
            objective=row["objective"],
            return_to=row["return_to"],
            allowed_domains=tuple(json.loads(row["allowed_domains"])),
            allowed_capabilities=tuple(json.loads(row["allowed_capabilities"])),
            forbidden_actions=tuple(json.loads(row["forbidden_actions"])),
            completion_criteria=tuple(json.loads(row["completion_criteria"])),
            max_autonomy=AutonomyLevel(row["max_autonomy"]),
            status=MissionStatus(row["status"]),
            version=row["version"],
            emergency_stopped=bool(row["emergency_stopped"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=json.loads(row["metadata"]),
        )

    def update_mission(self, mission: Mission, expected_version: int) -> Mission:
        now = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """UPDATE missions
                   SET status = ?, emergency_stopped = ?, version = version + 1, updated_at = ?, metadata = ?
                   WHERE mission_id = ? AND version = ?""",
                (
                    mission.status.value,
                    int(mission.emergency_stopped),
                    now,
                    self._json(mission.metadata),
                    mission.mission_id,
                    expected_version,
                ),
            )
            if cursor.rowcount != 1:
                connection.execute("ROLLBACK")
                raise ConcurrentUpdate(f"Versão divergente para {mission.mission_id}")
            connection.execute("COMMIT")
        return self.get_mission(mission.mission_id)

    def add_step(self, step: MissionStep) -> MissionStep:
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO mission_steps VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    step.step_id,
                    step.mission_id,
                    step.sequence,
                    step.action,
                    step.capability,
                    step.target,
                    self._json(step.parameters),
                    step.risk.value,
                    int(step.requires_approval),
                    step.approval_status.value,
                    step.status.value,
                    step.attempts,
                    step.version,
                    self._json(step.evidence),
                    step.sanitized_error,
                    step.created_at,
                    step.updated_at,
                ),
            )
        self.append_event(step.mission_id, "STEP_PLANNED", {"step_id": step.step_id, "sequence": step.sequence})
        return step

    def get_step(self, step_id: str) -> MissionStep:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM mission_steps WHERE step_id = ?", (step_id,)).fetchone()
        if row is None:
            raise MissionNotFound(step_id)
        return self._row_to_step(row)

    def list_steps(self, mission_id: str) -> list[MissionStep]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM mission_steps WHERE mission_id = ? ORDER BY sequence", (mission_id,)
            ).fetchall()
        return [self._row_to_step(row) for row in rows]

    def _row_to_step(self, row: sqlite3.Row) -> MissionStep:
        return MissionStep(
            step_id=row["step_id"],
            mission_id=row["mission_id"],
            sequence=row["sequence"],
            action=row["action"],
            capability=row["capability"],
            target=row["target"],
            parameters=json.loads(row["parameters"]),
            risk=RiskLevel(row["risk"]),
            requires_approval=bool(row["requires_approval"]),
            approval_status=ApprovalStatus(row["approval_status"]),
            status=StepStatus(row["status"]),
            attempts=row["attempts"],
            version=row["version"],
            evidence=tuple(json.loads(row["evidence"])),
            sanitized_error=row["sanitized_error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def update_step(self, step: MissionStep, expected_version: int) -> MissionStep:
        now = utc_now()
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """UPDATE mission_steps SET status = ?, approval_status = ?, attempts = ?, evidence = ?,
                   sanitized_error = ?, version = version + 1, updated_at = ?
                   WHERE step_id = ? AND version = ?""",
                (
                    step.status.value,
                    step.approval_status.value,
                    step.attempts,
                    self._json(step.evidence),
                    step.sanitized_error,
                    now,
                    step.step_id,
                    expected_version,
                ),
            )
            if cursor.rowcount != 1:
                connection.execute("ROLLBACK")
                raise ConcurrentUpdate(f"Versão divergente para etapa {step.step_id}")
            connection.execute("COMMIT")
        return self.get_step(step.step_id)

    def list_missions(self, statuses: tuple[MissionStatus, ...] | None = None) -> list[Mission]:
        query = "SELECT mission_id FROM missions"
        params: tuple[Any, ...] = ()
        if statuses:
            placeholders = ",".join("?" for _ in statuses)
            query += f" WHERE status IN ({placeholders})"
            params = tuple(status.value for status in statuses)
        query += " ORDER BY created_at"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self.get_mission(row["mission_id"]) for row in rows]

    def append_event(self, mission_id: str, event_type: str, payload: dict[str, Any]) -> MissionEvent:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            latest = connection.execute(
                "SELECT sequence, event_hash FROM mission_events WHERE mission_id = ? ORDER BY sequence DESC LIMIT 1",
                (mission_id,),
            ).fetchone()
            sequence = 1 if latest is None else latest["sequence"] + 1
            previous_hash = "0" * 64 if latest is None else latest["event_hash"]
            event = build_event(mission_id, event_type, sequence, payload, previous_hash)
            connection.execute(
                "INSERT INTO mission_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event.event_id,
                    event.mission_id,
                    event.sequence,
                    event.event_type,
                    self._json(event.payload),
                    event.previous_hash,
                    event.event_hash,
                    event.created_at,
                ),
            )
            connection.execute("COMMIT")
        return event

    def list_events(self, mission_id: str) -> list[MissionEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM mission_events WHERE mission_id = ? ORDER BY sequence", (mission_id,)
            ).fetchall()
        return [
            MissionEvent(
                row["event_id"], row["mission_id"], row["event_type"], row["sequence"],
                json.loads(row["payload"]), row["previous_hash"], row["event_hash"], row["created_at"]
            )
            for row in rows
        ]

    def save_approval(self, approval: Approval) -> Approval:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO approvals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    approval.approval_id,
                    approval.mission_id,
                    approval.step_id,
                    approval.status.value,
                    approval.requested_by,
                    approval.decided_by,
                    approval.reason,
                    approval.created_at,
                    approval.decided_at,
                ),
            )
        return approval

    def get_approval_for_step(self, step_id: str) -> Approval | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM approvals WHERE step_id = ? ORDER BY created_at DESC LIMIT 1", (step_id,)
            ).fetchone()
        if row is None:
            return None
        return Approval(
            row["approval_id"], row["mission_id"], row["step_id"], ApprovalStatus(row["status"]),
            row["requested_by"], row["decided_by"], row["reason"], row["created_at"], row["decided_at"]
        )

    def put_memory(self, key: str, value: dict[str, Any], sensitivity: str = "INTERNAL") -> None:
        if sensitivity == "SECRET":
            raise ValueError("Segredos não podem ser armazenados na memória operacional")
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO operational_memory VALUES (?, ?, ?, ?)",
                (key, self._json(value), sensitivity, utc_now()),
            )

    def get_memory(self, key: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT memory_value FROM operational_memory WHERE memory_key = ?", (key,)).fetchone()
        return None if row is None else json.loads(row["memory_value"])
