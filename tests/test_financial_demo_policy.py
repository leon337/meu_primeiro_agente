from __future__ import annotations

from app.missions.models import AutonomyLevel, Mission, MissionStep
from app.policies.engine import PolicyEngine


def make_demo_mission(**overrides: object) -> Mission:
    values: dict[str, object] = {
        "mission_id": "DEMO-1",
        "requester": "ChatService",
        "objective": "Testar interface demonstrativa",
        "return_to": "chat",
        "allowed_domains": ("olymptrade.com",),
        "allowed_capabilities": ("financial",),
        "completion_criteria": ("simulação concluída",),
        "max_autonomy": AutonomyLevel.HUMAN_ONLY,
        "metadata": {"owner_authorized": True, "demo_only": True},
    }
    values.update(overrides)
    return Mission(**values)  # type: ignore[arg-type]


def configure_demo(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("AEP_FINANCIAL_TEST_MODE", "1")
    monkeypatch.setenv("AEP_ALLOW_DEMO_ONLY", "1")
    monkeypatch.setenv("AEP_REAL_FINANCIAL_EFFECT", "0")
    monkeypatch.setenv("AEP_ALLOW_REAL_ORDER", "0")
    monkeypatch.setenv("AEP_ALLOW_DEPOSIT", "0")
    monkeypatch.setenv("AEP_ALLOW_WITHDRAWAL", "0")
    monkeypatch.setenv("AEP_FINANCIAL_DEMO_DOMAINS", "olymptrade.com")


def test_demo_financial_action_is_allowed_only_with_confirmation(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    configure_demo(monkeypatch)
    mission = make_demo_mission()
    step = MissionStep(
        "STEP-DEMO",
        mission.mission_id,
        1,
        "submit",
        "financial",
        "https://olymptrade.com/platform",
        parameters={"demo_only": True, "real_financial_effect": False},
    )

    decision = PolicyEngine().evaluate(mission, step)

    assert decision.allowed is True
    assert decision.requires_approval is True
    assert decision.code == "FINANCIAL_DEMO_CONFIRMATION"


def test_real_deposit_remains_blocked_in_demo_mode(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    configure_demo(monkeypatch)
    mission = make_demo_mission()
    step = MissionStep(
        "STEP-DEPOSIT",
        mission.mission_id,
        1,
        "deposit",
        "financial",
        "https://olymptrade.com/deposit",
        parameters={"demo_only": True},
    )

    decision = PolicyEngine().evaluate(mission, step)

    assert decision.allowed is False
    assert decision.code == "REAL_FINANCIAL_EFFECT_BLOCKED"


def test_demo_scope_is_required_on_mission_and_step(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    configure_demo(monkeypatch)
    mission = make_demo_mission(metadata={"owner_authorized": True, "demo_only": False})
    step = MissionStep(
        "STEP-NO-DEMO",
        mission.mission_id,
        1,
        "submit",
        "financial",
        "https://olymptrade.com/platform",
        parameters={"demo_only": True},
    )

    decision = PolicyEngine().evaluate(mission, step)

    assert decision.allowed is False
    assert decision.code == "DEMO_SCOPE_REQUIRED"


def test_unlisted_demo_domain_is_blocked(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    configure_demo(monkeypatch)
    mission = make_demo_mission(allowed_domains=("example.org",))
    step = MissionStep(
        "STEP-OTHER-DOMAIN",
        mission.mission_id,
        1,
        "submit",
        "financial",
        "https://example.org/demo",
        parameters={"demo_only": True},
    )

    decision = PolicyEngine().evaluate(mission, step)

    assert decision.allowed is False
    assert decision.code == "FINANCIAL_DEMO_DOMAIN_BLOCKED"
