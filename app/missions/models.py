"""Contratos persistentes do Agente Executivo Pessoal."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from typing import Any


class MissionStatus(StrEnum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_HUMAN = "WAITING_HUMAN"
    BLOCKED = "BLOCKED"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class StepStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_HUMAN = "WAITING_HUMAN"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AutonomyLevel(IntEnum):
    OBSERVE = 1
    PREPARE = 2
    EXECUTE_REVERSIBLE = 3
    CONFIRM_HIGH_IMPACT = 4
    HUMAN_ONLY = 5


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApprovalStatus(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(slots=True)
class Mission:
    mission_id: str
    requester: str
    objective: str
    return_to: str
    allowed_domains: tuple[str, ...] = ()
    allowed_capabilities: tuple[str, ...] = ()
    forbidden_actions: tuple[str, ...] = ()
    completion_criteria: tuple[str, ...] = ()
    max_autonomy: AutonomyLevel = AutonomyLevel.OBSERVE
    status: MissionStatus = MissionStatus.CREATED
    version: int = 1
    emergency_stopped: bool = False
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MissionStep:
    step_id: str
    mission_id: str
    sequence: int
    action: str
    capability: str
    target: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    risk: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    approval_status: ApprovalStatus = ApprovalStatus.NOT_REQUIRED
    status: StepStatus = StepStatus.PENDING
    attempts: int = 0
    version: int = 1
    evidence: tuple[dict[str, Any], ...] = ()
    sanitized_error: str = ""
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class MissionEvent:
    event_id: str
    mission_id: str
    event_type: str
    sequence: int
    payload: dict[str, Any]
    previous_hash: str
    event_hash: str
    created_at: str


@dataclass(frozen=True, slots=True)
class Approval:
    approval_id: str
    mission_id: str
    step_id: str
    status: ApprovalStatus
    requested_by: str
    decided_by: str = ""
    reason: str = ""
    created_at: str = field(default_factory=utc_now)
    decided_at: str = ""
