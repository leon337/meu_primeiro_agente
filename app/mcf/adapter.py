"""Contrato explícito entre o MCF e o Agente Executivo Pessoal."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from app.audit.receipts import create_receipt
from app.missions.models import AutonomyLevel, Mission, MissionStep, RiskLevel
from app.missions.service import MissionService


@dataclass(frozen=True, slots=True)
class MCFTaskRequest:
    mission_id: str
    requester_agent: str
    objective: str
    return_to: str
    allowed_domains: tuple[str, ...]
    allowed_capabilities: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    completion_criteria: tuple[str, ...]
    max_autonomy: int = 1

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "MCFTaskRequest":
        required = {
            "mission_id", "requester_agent", "objective", "return_to",
            "allowed_domains", "allowed_capabilities", "completion_criteria",
        }
        missing = sorted(required - payload.keys())
        if missing:
            raise ValueError("Campos MCF ausentes: " + ", ".join(missing))
        return cls(
            mission_id=str(payload["mission_id"]),
            requester_agent=str(payload["requester_agent"]),
            objective=str(payload["objective"]),
            return_to=str(payload["return_to"]),
            allowed_domains=tuple(str(item) for item in payload["allowed_domains"]),
            allowed_capabilities=tuple(str(item) for item in payload["allowed_capabilities"]),
            forbidden_actions=tuple(str(item) for item in payload.get("forbidden_actions", ())),
            completion_criteria=tuple(str(item) for item in payload["completion_criteria"]),
            max_autonomy=int(payload.get("max_autonomy", 1)),
        )


class MCFAdapter:
    def __init__(self, service: MissionService, signing_key: str | None = None) -> None:
        self.service = service
        self.signing_key = signing_key

    @staticmethod
    def _mission_from_request(request: MCFTaskRequest) -> Mission:
        return Mission(
            mission_id=request.mission_id,
            requester=request.requester_agent,
            objective=request.objective,
            return_to=request.return_to,
            allowed_domains=request.allowed_domains,
            allowed_capabilities=request.allowed_capabilities,
            forbidden_actions=request.forbidden_actions,
            completion_criteria=request.completion_criteria,
            max_autonomy=AutonomyLevel(request.max_autonomy),
            metadata={"source": "MCF", "contract_version": 1},
        )

    def accept(self, request: MCFTaskRequest) -> Mission:
        candidate = self._mission_from_request(request)
        try:
            existing = self.service.repository.get_mission(request.mission_id)
        except KeyError:
            return self.service.create(candidate)
        contract_fields = (
            "requester", "objective", "return_to", "allowed_domains", "allowed_capabilities",
            "forbidden_actions", "completion_criteria", "max_autonomy", "metadata",
        )
        if all(getattr(existing, field) == getattr(candidate, field) for field in contract_fields):
            return existing
        raise ValueError("Identificador de missão já existe com contrato divergente")

    def add_step(
        self,
        mission_id: str,
        sequence: int,
        action: str,
        capability: str,
        target: str = "",
        parameters: dict[str, Any] | None = None,
        risk: RiskLevel = RiskLevel.LOW,
    ) -> MissionStep:
        normalized_parameters = parameters or {}
        for existing in self.service.repository.list_steps(mission_id):
            if existing.sequence != sequence:
                continue
            if (
                existing.action == action
                and existing.capability == capability
                and existing.target == target
                and existing.parameters == normalized_parameters
            ):
                return existing
            raise ValueError("Sequência de etapa já existe com plano divergente")
        return self.service.add_step(
            MissionStep(
                step_id=str(uuid4()),
                mission_id=mission_id,
                sequence=sequence,
                action=action,
                capability=capability,
                target=target,
                parameters=normalized_parameters,
                risk=risk,
            )
        )

    def result_packet(self, mission_id: str) -> dict[str, Any]:
        mission = self.service.repository.get_mission(mission_id)
        steps = self.service.repository.list_steps(mission_id)
        events = self.service.repository.list_events(mission_id)
        payload = {
            "mission_id": mission_id,
            "status": mission.status.value,
            "return_to": mission.return_to,
            "objective": mission.objective,
            "steps": [
                {
                    "step_id": step.step_id,
                    "sequence": step.sequence,
                    "status": step.status.value,
                    "evidence_count": len(step.evidence),
                    "error": step.sanitized_error,
                }
                for step in steps
            ],
            "event_head": events[-1].event_hash if events else None,
            "event_count": len(events),
        }
        return create_receipt(payload, self.signing_key)
