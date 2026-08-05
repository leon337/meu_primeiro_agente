from pathlib import Path

from app.mcf.adapter import MCFAdapter, MCFTaskRequest
from app.missions.models import MissionStatus
from app.missions.repository import SQLiteMissionRepository
from app.missions.service import MissionService
from app.policies.engine import PolicyEngine


def test_result_packet_returns_sanitized_executor_evidence(tmp_path: Path) -> None:
    service = MissionService(SQLiteMissionRepository(tmp_path / "aep.sqlite3"), PolicyEngine())
    adapter = MCFAdapter(service, "signing-key")
    request = MCFTaskRequest(
        mission_id="CHAT-EVIDENCE-1",
        requester_agent="ChatService",
        objective="Ler texto da página",
        return_to="chat",
        allowed_domains=("example.com",),
        allowed_capabilities=("observe",),
        forbidden_actions=(),
        completion_criteria=("texto devolvido",),
        max_autonomy=4,
        owner_authorized=True,
    )

    adapter.accept(request)
    service.transition(request.mission_id, MissionStatus.PLANNING)
    step = adapter.add_step(
        request.mission_id,
        1,
        "read_text",
        "observe",
        "https://example.com",
        {"channel": "browser", "selector": "h1"},
    )
    service.transition(request.mission_id, MissionStatus.READY)
    service.transition(request.mission_id, MissionStatus.RUNNING)
    service.execute_step(step.step_id, lambda _mission, _step: {"text": "Example Domain"})
    service.transition(request.mission_id, MissionStatus.COMPLETED)

    packet = adapter.result_packet(request.mission_id)
    step_packet = packet["payload"]["steps"][0]

    assert packet["payload"]["owner_authorized"] is True
    assert step_packet["evidence_count"] == 1
    assert step_packet["evidence"][0]["data"]["text"] == "Example Domain"
    assert packet["signature"] is not None
