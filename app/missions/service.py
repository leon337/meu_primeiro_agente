"""Serviço de aplicação para o loop orientado a objetivo."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable
from uuid import uuid4

from app.missions.models import (
    Approval,
    ApprovalStatus,
    Mission,
    MissionStatus,
    MissionStep,
    StepStatus,
    utc_now,
)
from app.missions.repository import SQLiteMissionRepository
from app.missions.state_machine import validate_mission_transition, validate_step_transition
from app.policies.engine import PolicyDecision, PolicyEngine


class MissionValidationError(ValueError):
    pass


FORBIDDEN_METADATA_KEYS = {
    "password", "senha", "token", "cookie", "api_key", "secret", "authorization", "credential"
}


class MissionService:
    def __init__(self, repository: SQLiteMissionRepository, policy_engine: PolicyEngine) -> None:
        self.repository = repository
        self.policy_engine = policy_engine

    def create(self, mission: Mission) -> Mission:
        self._validate_mission(mission)
        return self.repository.create_mission(mission)

    def _validate_mission(self, mission: Mission) -> None:
        if not mission.mission_id.strip() or not mission.requester.strip() or not mission.objective.strip():
            raise MissionValidationError("Identificador, solicitante e objetivo são obrigatórios")
        if not mission.return_to.strip() or not mission.completion_criteria:
            raise MissionValidationError("Destino de retorno e critérios de conclusão são obrigatórios")
        lowered = {str(key).lower() for key in mission.metadata}
        if lowered & FORBIDDEN_METADATA_KEYS:
            raise MissionValidationError("Credenciais e segredos não podem integrar o contrato da missão")

    def transition(self, mission_id: str, target: MissionStatus, expected_version: int | None = None) -> Mission:
        mission = self.repository.get_mission(mission_id)
        if mission.emergency_stopped and target not in {MissionStatus.CANCELLED, MissionStatus.FAILED}:
            raise MissionValidationError("Missão parada por emergência")
        validate_mission_transition(mission.status, target)
        expected = mission.version if expected_version is None else expected_version
        updated = self.repository.update_mission(replace(mission, status=target), expected)
        self.repository.append_event(mission_id, "MISSION_TRANSITIONED", {"from": mission.status, "to": target})
        return updated

    def add_step(self, step: MissionStep) -> MissionStep:
        mission = self.repository.get_mission(step.mission_id)
        self._validate_step_parameters(step.parameters)
        if mission.status not in {MissionStatus.PLANNING, MissionStatus.RECOVERING}:
            raise MissionValidationError("Etapas só podem ser adicionadas durante planejamento ou recuperação")
        if mission.emergency_stopped:
            raise MissionValidationError("Não é possível planejar após parada de emergência")
        if step.capability not in mission.allowed_capabilities:
            raise MissionValidationError(f"Capacidade fora do contrato: {step.capability}")
        decision = self.policy_engine.evaluate(mission, step)
        normalized = replace(
            step,
            risk=decision.risk,
            requires_approval=decision.requires_approval,
            approval_status=ApprovalStatus.PENDING if decision.requires_approval else ApprovalStatus.NOT_REQUIRED,
            status=StepStatus.BLOCKED if not decision.allowed else step.status,
        )
        stored = self.repository.add_step(normalized)
        self.repository.append_event(
            mission.mission_id,
            "POLICY_EVALUATED",
            {"step_id": step.step_id, "decision": decision.code, "allowed": decision.allowed},
        )
        return stored

    @staticmethod
    def _validate_step_parameters(parameters: dict[str, Any]) -> None:
        serialized = str(parameters)
        if len(serialized) > 16000:
            raise MissionValidationError("Parâmetros da etapa excedem o limite")
        forbidden = {"password", "senha", "token", "cookie", "api_key", "secret", "authorization", "credential_value"}
        stack: list[Any] = [parameters]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for key, value in current.items():
                    if str(key).casefold() in forbidden:
                        raise MissionValidationError("Segredos devem ser referenciados pelo corretor local, nunca enviados na missão")
                    stack.append(value)
            elif isinstance(current, (list, tuple)):
                stack.extend(current)

    def request_approval(self, step_id: str, requested_by: str) -> Approval:
        step = self.repository.get_step(step_id)
        approval = Approval(str(uuid4()), step.mission_id, step.step_id, ApprovalStatus.PENDING, requested_by)
        self.repository.save_approval(approval)
        if step.status != StepStatus.WAITING_HUMAN:
            validate_step_transition(step.status, StepStatus.WAITING_HUMAN)
            self.repository.update_step(replace(step, status=StepStatus.WAITING_HUMAN), step.version)
        mission = self.repository.get_mission(step.mission_id)
        if mission.status == MissionStatus.RUNNING:
            self.transition(mission.mission_id, MissionStatus.WAITING_HUMAN)
        self.repository.append_event(step.mission_id, "HUMAN_APPROVAL_REQUESTED", {"step_id": step.step_id})
        return approval

    def decide_approval(self, step_id: str, approved: bool, decided_by: str, reason: str = "") -> Approval:
        current = self.repository.get_approval_for_step(step_id)
        if current is None or current.status != ApprovalStatus.PENDING:
            raise MissionValidationError("Não existe aprovação pendente para a etapa")
        status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        decision = replace(current, status=status, decided_by=decided_by, reason=reason, decided_at=utc_now())
        self.repository.save_approval(decision)
        step = self.repository.get_step(step_id)
        target = StepStatus.PENDING if approved else StepStatus.BLOCKED
        validate_step_transition(step.status, target)
        updated = replace(step, status=target, approval_status=status)
        self.repository.update_step(updated, step.version)
        mission = self.repository.get_mission(step.mission_id)
        if approved and mission.status == MissionStatus.WAITING_HUMAN:
            self.transition(mission.mission_id, MissionStatus.RUNNING)
        self.repository.append_event(step.mission_id, "HUMAN_APPROVAL_DECIDED", {"step_id": step_id, "approved": approved})
        return decision

    def execute_step(
        self,
        step_id: str,
        executor: Callable[[Mission, MissionStep], dict[str, Any]],
    ) -> MissionStep:
        step = self.repository.get_step(step_id)
        mission = self.repository.get_mission(step.mission_id)
        if mission.emergency_stopped or mission.status in {MissionStatus.CANCELLED, MissionStatus.FAILED}:
            raise MissionValidationError("Missão não aceita novas ações")
        decision: PolicyDecision = self.policy_engine.evaluate(mission, step)
        if not decision.allowed:
            blocked = replace(step, status=StepStatus.BLOCKED, sanitized_error=decision.reason)
            return self.repository.update_step(blocked, step.version)
        if decision.requires_approval:
            approval = self.repository.get_approval_for_step(step.step_id)
            if approval is None or approval.status != ApprovalStatus.APPROVED:
                self.request_approval(step.step_id, mission.requester)
                return self.repository.get_step(step.step_id)
        if step.status not in {StepStatus.PENDING, StepStatus.BLOCKED}:
            raise MissionValidationError(f"Etapa não executável no estado {step.status}")
        running = self.repository.update_step(
            replace(step, status=StepStatus.RUNNING, attempts=step.attempts + 1), step.version
        )
        self.repository.append_event(step.mission_id, "STEP_STARTED", {"step_id": step.step_id})
        try:
            output = executor(mission, running)
        except Exception as exc:
            failed = replace(running, status=StepStatus.FAILED, sanitized_error=self._sanitize_error(exc))
            stored = self.repository.update_step(failed, running.version)
            self.repository.append_event(step.mission_id, "STEP_FAILED", {"step_id": step.step_id})
            return stored
        evidence = tuple((*running.evidence, {"kind": "executor_result", "data": output, "created_at": utc_now()}))
        completed = replace(running, status=StepStatus.COMPLETED, evidence=evidence)
        stored = self.repository.update_step(completed, running.version)
        self.repository.append_event(step.mission_id, "STEP_COMPLETED", {"step_id": step.step_id})
        return stored

    @staticmethod
    def _sanitize_error(exc: Exception) -> str:
        message = str(exc).replace("\n", " ").strip()
        return (message[:240] or exc.__class__.__name__)

    def emergency_stop(self, mission_id: str, actor: str, reason: str) -> Mission:
        mission = self.repository.get_mission(mission_id)
        stopped = self.repository.update_mission(replace(mission, emergency_stopped=True), mission.version)
        for step in self.repository.list_steps(mission_id):
            if step.status in {StepStatus.PENDING, StepStatus.RUNNING, StepStatus.WAITING_HUMAN, StepStatus.BLOCKED}:
                self.repository.update_step(replace(step, status=StepStatus.CANCELLED), step.version)
        self.repository.append_event(mission_id, "EMERGENCY_STOP", {"actor": actor, "reason": reason[:240]})
        if stopped.status not in {MissionStatus.COMPLETED, MissionStatus.FAILED, MissionStatus.CANCELLED}:
            try:
                stopped = self.transition(mission_id, MissionStatus.CANCELLED)
            except Exception:
                stopped = self.repository.get_mission(mission_id)
        return stopped
