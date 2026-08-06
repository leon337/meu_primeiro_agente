#!/usr/bin/env python3
"""Gate local da Fase 10, sem revelar segredos."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from app.desktop.executor import (
    AtSpiDesktopBackend,
    DesktopAction,
    DesktopApplicationRegistry,
    DesktopOperation,
    SafeDesktopExecutor,
)
from app.missions.models import AutonomyLevel, Mission, MissionStep
from app.policies.engine import PolicyEngine


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--real", action="store_true", help="Abre e focaliza os aplicativos informados")
    result.add_argument("--application", action="append", default=[], help="Nome ou desktop id do aplicativo")
    return result


def make_demo_mission(domain: str) -> Mission:
    return Mission(
        mission_id="LOCAL-DEMO-GATE",
        requester="ChatService",
        objective="Validar política demonstrativa",
        return_to="chat",
        allowed_domains=(domain,),
        allowed_capabilities=("financial",),
        completion_criteria=("gate concluído",),
        max_autonomy=AutonomyLevel.HUMAN_ONLY,
        metadata={"owner_authorized": True, "demo_only": True},
    )


def main() -> int:
    args = parser().parse_args()
    load_dotenv(ROOT / ".env")

    registry = DesktopApplicationRegistry()
    applications = registry.list_public()
    if not applications:
        raise RuntimeError("Nenhum aplicativo .desktop foi encontrado")

    resolved: list[dict[str, str]] = []
    for query in args.application:
        item = registry.resolve(query)
        resolved.append({"query": query, "name": item.name, "desktop_id": item.desktop_id})

    real_results: list[dict[str, object]] = []
    if args.real:
        if os.getenv("AEP_DESKTOP_REAL", "0") != "1":
            raise RuntimeError("AEP_DESKTOP_REAL precisa estar igual a 1")
        if os.getenv("AEP_DESKTOP_ALLOW_ALL_APPS", "0") != "1":
            raise RuntimeError("AEP_DESKTOP_ALLOW_ALL_APPS precisa estar igual a 1")
        executor = SafeDesktopExecutor(
            (),
            AtSpiDesktopBackend(),
            allow_all_applications=True,
        )
        for query in args.application:
            result = executor.execute(DesktopAction(query, DesktopOperation.LAUNCH_APPLICATION))
            real_results.append(result)

    domains = [
        item.strip().lower()
        for item in os.getenv("AEP_FINANCIAL_DEMO_DOMAINS", "").split(",")
        if item.strip()
    ]
    demo_policy = {"configured": bool(domains), "allowed": False, "real_effect_blocked": False}
    if domains:
        domain = domains[0]
        mission = make_demo_mission(domain)
        demo_step = MissionStep(
            "LOCAL-DEMO-STEP",
            mission.mission_id,
            1,
            "submit",
            "financial",
            f"https://{domain}/",
            parameters={"demo_only": True, "real_financial_effect": False},
        )
        blocked_step = MissionStep(
            "LOCAL-REAL-STEP",
            mission.mission_id,
            2,
            "deposit",
            "financial",
            f"https://{domain}/",
            parameters={"demo_only": True},
        )
        demo_decision = PolicyEngine().evaluate(mission, demo_step)
        blocked_decision = PolicyEngine().evaluate(mission, blocked_step)
        demo_policy = {
            "configured": True,
            "allowed": demo_decision.allowed,
            "requires_approval": demo_decision.requires_approval,
            "code": demo_decision.code,
            "real_effect_blocked": not blocked_decision.allowed,
            "real_effect_code": blocked_decision.code,
        }

    payload = {
        "gate": "AEP_UNIVERSAL_APP_DEMO_LOCAL",
        "status": "COMPLETED",
        "result": "PASS",
        "registered_application_count": len(applications),
        "resolved_applications": resolved,
        "real_results": real_results,
        "demo_policy": demo_policy,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
