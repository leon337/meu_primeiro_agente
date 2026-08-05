from __future__ import annotations

from app.bridge import MissionCreateRequest
from app.mcf.adapter import MCFAdapter, MCFTaskRequest
from app.missions.models import AutonomyLevel, Mission, MissionStep
from app.policies.engine import PolicyEngine
from app.providers.gemini_provider import GeminiProvider
from app.tools.remote import executive_tool_definitions


def make_owner_mission(**overrides: object) -> Mission:
    values: dict[str, object] = {
        "mission_id": "CHAT-OWNER-1",
        "requester": "ChatService",
        "objective": "Publicar configuração autorizada",
        "return_to": "chat",
        "allowed_domains": ("example.com",),
        "allowed_capabilities": ("publish", "shell"),
        "completion_criteria": ("ação concluída",),
        "max_autonomy": AutonomyLevel.CONFIRM_HIGH_IMPACT,
        "metadata": {"owner_authorized": True},
    }
    values.update(overrides)
    return Mission(**values)  # type: ignore[arg-type]


def test_owner_authorized_high_impact_does_not_require_per_step_approval() -> None:
    mission = make_owner_mission()
    step = MissionStep(
        "STEP-PUBLISH",
        mission.mission_id,
        1,
        "submit",
        "publish",
        "https://example.com/settings",
    )

    decision = PolicyEngine().evaluate(mission, step)

    assert decision.allowed is True
    assert decision.requires_approval is False
    assert decision.code == "OWNER_AUTHORIZED"


def test_owner_authorization_is_bound_to_authenticated_chat_identity() -> None:
    mission = make_owner_mission(requester="OutroAgente")
    step = MissionStep(
        "STEP-PUBLISH",
        mission.mission_id,
        1,
        "submit",
        "publish",
        "https://example.com/settings",
    )

    decision = PolicyEngine().evaluate(mission, step)

    assert decision.allowed is True
    assert decision.requires_approval is True
    assert decision.code == "HUMAN_CONFIRMATION"


def test_owner_authorization_does_not_override_human_only_capability() -> None:
    mission = make_owner_mission()
    step = MissionStep("STEP-SHELL", mission.mission_id, 1, "run", "shell")

    decision = PolicyEngine().evaluate(mission, step)

    assert decision.allowed is False
    assert decision.code == "HUMAN_ONLY"


def test_mcf_contract_persists_owner_authorization() -> None:
    request = MCFTaskRequest(
        mission_id="CHAT-CONTRACT-1",
        requester_agent="ChatService",
        objective="Executar ação autorizada",
        return_to="chat",
        allowed_domains=("example.com",),
        allowed_capabilities=("publish",),
        forbidden_actions=(),
        completion_criteria=("concluído",),
        max_autonomy=4,
        owner_authorized=True,
    )

    mission = MCFAdapter._mission_from_request(request)

    assert mission.metadata["owner_authorized"] is True
    assert mission.metadata["contract_version"] == 2


def test_bridge_request_retains_owner_authorization() -> None:
    payload = MissionCreateRequest(
        mission_id="CHAT-BRIDGE-1",
        requester_agent="ChatService",
        objective="Executar ação autorizada",
        return_to="chat",
        allowed_domains=["example.com"],
        allowed_capabilities=["observe"],
        completion_criteria=["concluído"],
        max_autonomy=4,
        owner_authorized=True,
    )

    assert payload.model_dump()["owner_authorized"] is True


def test_gemini_accepts_executive_tool_schemas() -> None:
    provider = GeminiProvider(
        api_key="fake-key",
        model_name="gemini-3.6-flash",
        tools=executive_tool_definitions(),
    )

    declarations = provider._config.tools[0].function_declarations  # type: ignore[attr-defined]
    assert {item.name for item in declarations} == {
        "aep_submit_mission",
        "aep_get_mission",
        "aep_approve_step",
        "aep_emergency_stop",
    }
