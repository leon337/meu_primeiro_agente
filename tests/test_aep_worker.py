from pathlib import Path

from app.missions.models import AutonomyLevel, Mission, MissionStatus, MissionStep
from app.missions.repository import SQLiteMissionRepository
from app.missions.service import MissionService
from app.policies.engine import PolicyEngine
from app.runtime.worker import AutonomousWorker


def test_worker_completes_bounded_mission(tmp_path: Path) -> None:
    service = MissionService(SQLiteMissionRepository(tmp_path / "db.sqlite3"), PolicyEngine())
    mission = service.create(Mission(
        mission_id="MCF-WORKER-1",
        requester="Mestre",
        objective="Executar consulta",
        return_to="Mestre",
        allowed_domains=("vercel.com",),
        allowed_capabilities=("observe",),
        completion_criteria=("consulta concluída",),
        max_autonomy=AutonomyLevel.OBSERVE,
    ))
    service.transition(mission.mission_id, MissionStatus.PLANNING)
    service.add_step(MissionStep("step-1", mission.mission_id, 1, "navigate", "observe", "https://vercel.com"))
    service.transition(mission.mission_id, MissionStatus.READY)
    worker = AutonomousWorker(service, {"observe": lambda _m, _s: {"status": "ok"}}, poll_interval=0)
    stats = worker.run_mission(mission.mission_id)
    assert stats.completed_steps == 1
    assert service.repository.get_mission(mission.mission_id).status == MissionStatus.COMPLETED
