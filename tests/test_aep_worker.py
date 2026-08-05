from pathlib import Path

from app.missions.models import AutonomyLevel, Mission, MissionStatus, MissionStep, StepStatus
from app.missions.repository import SQLiteMissionRepository
from app.missions.service import MissionService
from app.policies.engine import PolicyEngine
from app.runtime.worker import AutonomousWorker


def make_worker_mission(service: MissionService, mission_id: str, capability: str = "observe") -> Mission:
    mission = service.create(Mission(
        mission_id=mission_id,
        requester="Mestre",
        objective="Executar consulta",
        return_to="Mestre",
        allowed_domains=("vercel.com",),
        allowed_capabilities=(capability,),
        completion_criteria=("consulta concluída",),
        max_autonomy=AutonomyLevel.OBSERVE,
    ))
    service.transition(mission.mission_id, MissionStatus.PLANNING)
    service.add_step(MissionStep("step-" + mission_id, mission.mission_id, 1, "navigate", capability, "https://vercel.com"))
    service.transition(mission.mission_id, MissionStatus.READY)
    return mission


def test_worker_completes_bounded_mission(tmp_path: Path) -> None:
    service = MissionService(SQLiteMissionRepository(tmp_path / "db.sqlite3"), PolicyEngine())
    mission = make_worker_mission(service, "MCF-WORKER-1")
    worker = AutonomousWorker(service, {"observe": lambda _m, _s: {"status": "ok"}}, poll_interval=0)
    stats = worker.run_mission(mission.mission_id)
    assert stats.completed_steps == 1
    assert service.repository.get_mission(mission.mission_id).status == MissionStatus.COMPLETED


def test_worker_fails_mission_when_executor_is_missing(tmp_path: Path) -> None:
    service = MissionService(SQLiteMissionRepository(tmp_path / "db.sqlite3"), PolicyEngine())
    mission = make_worker_mission(service, "MCF-WORKER-2")
    worker = AutonomousWorker(service, {}, poll_interval=0)
    stats = worker.run_mission(mission.mission_id)
    step = service.repository.list_steps(mission.mission_id)[0]
    assert stats.failed_steps == 1
    assert step.status == StepStatus.FAILED
    assert "Executor não registrado" in step.sanitized_error
    assert service.repository.get_mission(mission.mission_id).status == MissionStatus.FAILED
