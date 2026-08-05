"""Adapta etapas do runtime para planos declarativos de navegador."""

from __future__ import annotations

from app.browser.executor import PlaywrightBrowserExecutor
from app.browser.models import BrowserAction, BrowserOperation
from app.missions.models import Mission, MissionStep


class BrowserStepAdapter:
    def __init__(self, executor: PlaywrightBrowserExecutor) -> None:
        self.executor = executor

    def __call__(self, mission: Mission, step: MissionStep) -> dict[str, object]:
        operation = BrowserOperation(step.action)
        action = BrowserAction(
            operation=operation,
            url=step.target if operation == BrowserOperation.NAVIGATE else "",
            selector=str(step.parameters.get("selector", "")),
            value=str(step.parameters.get("value", "")),
            credential_ref=str(step.parameters.get("credential_ref", "")),
            options=dict(step.parameters.get("options", {})),
        )
        actions: list[BrowserAction] = []
        if operation != BrowserOperation.NAVIGATE:
            if not step.target:
                raise ValueError("Ação de navegador exige URL de destino no contrato da etapa")
            actions.append(BrowserAction(BrowserOperation.NAVIGATE, url=step.target))
        actions.append(action)
        approval_granted = step.approval_status.value == "APPROVED" or not step.requires_approval
        return self.executor.execute(actions, approval_granted=approval_granted)
