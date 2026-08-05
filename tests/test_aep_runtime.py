from dataclasses import replace
from pathlib import Path

import pytest

from app.audit.ledger import validate_event_chain
from app.audit.receipts import verify_receipt
from app.mcf.adapter import MCFAdapter, MCFTaskRequest
from app.missions.models import (
    ApprovalStatus,
    AutonomyLevel,
    Mission,
    MissionStatus,
    MissionStep,
    StepStatus,
)
from app.missions.repository import ConcurrentUpdate, SQLiteMissionRepository
from app.missions.service import MissionService, MissionValidationError
from app.missions.state_machine import InvalidTransition
from app.policies.engine import PolicyEngine


def make_service(tmp_path: Path) -> MissionService:
    return MissionService(SQLiteMissionRepository(tmp_path / "aep.sqlite3"), PolicyEngine())


def make_mission(mission_id: str = "MCF-TEST-001") -> Mission:
    return Mission(
        mission_id=mission_id,
        requester="Bruno",
        objective="Consultar o último deploy",
        return_to="Mestre",
        allowed_domains=("vercel.com",),
        allowed_capabilities=("observe", "prepare", "execute_reversible", "publish"),
        forbidden_actions=("delete_project",),
        completion_criteria=("status retornado",),
        max_autonomy=AutonomyLevel.EXECUTE_REVERSIBLE,
    )


def test_persistent_mission_lifecycle_and_event_chain(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    created = service.create(make_mission())
    planning = service.transition(created.mission_id, MissionStatus.PLANNING)
    event_count = len(service.repository.list_events(created.mission_id))
    repeated = service.transition(created.mission_id, MissionStatus.PLANNING)
    assert repeated.version == planning.version
    assert len(service.repository.list_events(created.mission_id)) == event_count
    service.transition(created.mission_id, MissionStatus.READY)
    reloaded = make_service(tmp_path).repository.get_mission(created.mission_id)
    assert reloaded.status == MissionStatus.READY
    assert validate_event_chain(service.repository.list_events(created.mission_id))


def test_invalid_transition_and_optimistic_lock(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    mission = service.create(make_mission())
    with pytest.raises(InvalidTransition):
        service.transition(mission.mission_id, MissionStatus.COMPLETED)
    stale = service.repository.get_mission(mission.mission_id)
    service.transition(mission.mission_id, MissionStatus.PLANNING)
    with pytest.raises(ConcurrentUpdate):
        service.repository.update_mission(replace(stale, status=MissionStatus.CANCELLED), stale.version)
    with pytest.raises(ConcurrentUpdate):
        service.transition(mission.mission_id, MissionStatus.PLANNING, expected_version=stale.version)


def test_secret_fields_are_rejected(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    with pytest.raises(MissionValidationError, match="Credenciais"):
        service.create(replace(make_mission(), metadata={"password": "nao-guardar"}))


def test_policy_blocks_domain_and_human_only_capability(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    mission = service.create(make_mission())
    service.transition(mission.mission_id, MissionStatus.PLANNING)
    blocked = service.add_step(
        MissionStep(
            step_id="s1",
            mission_id=mission.mission_id,
            sequence=1,
            action="navigate",
            capability="observe",
            target="https://example.com",
        )
    )
    assert blocked.status == StepStatus.BLOCKED

    human_only_mission = replace(make_mission("MCF-TEST-002"), allowed_capabilities=("financial",))
    service.create(human_only_mission)
    service.transition(human_only_mission.mission_id, MissionStatus.PLANNING)
    financial = service.add_step(
        MissionStep("s2", human_only_mission.mission_id, 1, "pay", "financial", "https://vercel.com")
    )
    assert financial.status == StepStatus.BLOCKED
    assert financial.requires_approval


def test_approval_gate_and_execution(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    mission = service.create(make_mission())
    service.transition(mission.mission_id, MissionStatus.PLANNING)
    step = service.add_step(
        MissionStep("publish-1", mission.mission_id, 1, "submit", "publish", "https://vercel.com")
    )
    service.transition(mission.mission_id, MissionStatus.READY)
    service.transition(mission.mission_id, MissionStatus.RUNNING)
    waiting = service.execute_step(step.step_id, lambda _m, _s: {"ok": True})
    assert waiting.status == StepStatus.WAITING_HUMAN
    approval = service.decide_approval(step.step_id, True, "Leandro")
    event_count = len(service.repository.list_events(mission.mission_id))
    repeated = service.decide_approval(step.step_id, True, "Leandro")
    assert repeated.approval_id == approval.approval_id
    assert len(service.repository.list_events(mission.mission_id)) == event_count
    completed = service.execute_step(step.step_id, lambda _m, _s: {"ok": True})
    assert completed.status == StepStatus.COMPLETED
    assert completed.approval_status == ApprovalStatus.APPROVED


def test_emergency_stop_cancels_open_steps(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    mission = service.create(make_mission())
    service.transition(mission.mission_id, MissionStatus.PLANNING)
    service.add_step(MissionStep("s1", mission.mission_id, 1, "navigate", "observe", "https://vercel.com"))
    service.transition(mission.mission_id, MissionStatus.READY)
    stopped = service.emergency_stop(mission.mission_id, "Leandro", "teste")
    event_count = len(service.repository.list_events(mission.mission_id))
    repeated = service.emergency_stop(mission.mission_id, "Leandro", "teste repetido")
    assert repeated.version == stopped.version
    assert len(service.repository.list_events(mission.mission_id)) == event_count
    assert stopped.emergency_stopped
    assert service.repository.list_steps(mission.mission_id)[0].status == StepStatus.CANCELLED


def make_mcf_request() -> MCFTaskRequest:
    return MCFTaskRequest(
        mission_id="MCF-AEP-900",
        requester_agent="Bruno",
        objective="Consultar deploy",
        return_to="Mestre",
        allowed_domains=("vercel.com",),
        allowed_capabilities=("observe",),
        forbidden_actions=(),
        completion_criteria=("resultado",),
        max_autonomy=1,
    )


def test_mcf_adapter_and_receipt(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    adapter = MCFAdapter(service, "assinatura-local")
    request = make_mcf_request()
    adapter.accept(request)
    packet = adapter.result_packet(request.mission_id)
    assert verify_receipt(packet, "assinatura-local")


def test_mcf_contract_and_step_are_idempotent(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    adapter = MCFAdapter(service)
    request = make_mcf_request()
    first = adapter.accept(request)
    second = adapter.accept(request)
    assert first.mission_id == second.mission_id
    assert len(service.repository.list_events(request.mission_id)) == 1

    service.transition(request.mission_id, MissionStatus.PLANNING)
    first_step = adapter.add_step(
        request.mission_id,
        1,
        "read_text",
        "observe",
        "https://vercel.com/dashboard",
        {"selector": "h1"},
    )
    second_step = adapter.add_step(
        request.mission_id,
        1,
        "read_text",
        "observe",
        "https://vercel.com/dashboard",
        {"selector": "h1"},
    )
    assert first_step.step_id == second_step.step_id
    assert len(service.repository.list_steps(request.mission_id)) == 1

    with pytest.raises(ValueError, match="contrato divergente"):
        adapter.accept(replace(request, objective="Objetivo diferente"))
    with pytest.raises(ValueError, match="plano divergente"):
        adapter.add_step(request.mission_id, 1, "click", "observe", "https://vercel.com", {"selector": "button"})


def test_operational_memory_rejects_secrets(tmp_path: Path) -> None:
    repository = SQLiteMissionRepository(tmp_path / "aep.sqlite3")
    repository.put_memory("mission:x", {"status": "ok"})
    assert repository.get_memory("mission:x") == {"status": "ok"}
    with pytest.raises(ValueError, match="Segredos"):
        repository.put_memory("secret:x", {"token": "x"}, "SECRET")
