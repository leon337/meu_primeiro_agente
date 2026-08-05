"""Roteamento controlado entre navegador e aplicativos do desktop."""

from __future__ import annotations

import os
from pathlib import Path

from app.browser.adapter import BrowserStepAdapter
from app.browser.executor import EnvironmentCredentialBroker, PlaywrightBrowserExecutor
from app.desktop.executor import (
    AtSpiDesktopBackend,
    DesktopAction,
    DesktopOperation,
    DryRunDesktopBackend,
    SafeDesktopExecutor,
)
from app.missions.models import Mission, MissionStep


class ExecutiveActionExecutor:
    def __init__(self) -> None:
        self._browser_executor: PlaywrightBrowserExecutor | None = None
        self._browser_configuration: tuple[object, ...] | None = None

    def __call__(self, mission: Mission, step: MissionStep) -> dict[str, object]:
        channel = str(step.parameters.get("channel", "browser"))
        if channel == "browser":
            return self._browser(mission, step)
        if channel == "desktop":
            return self._desktop(mission, step)
        raise RuntimeError("Canal executivo não permitido")

    def close(self) -> None:
        if self._browser_executor is not None:
            self._browser_executor.close()
            self._browser_executor = None
            self._browser_configuration = None

    def _browser(self, mission: Mission, step: MissionStep) -> dict[str, object]:
        real = os.getenv("AEP_BROWSER_REAL", "0") == "1"
        profile = os.getenv("AEP_BROWSER_PROFILE", "var/aep/browser-profile")
        headless = os.getenv("AEP_BROWSER_HEADLESS", "0") == "1"
        keep_open = os.getenv("AEP_BROWSER_KEEP_OPEN", "1") == "1"
        configuration: tuple[object, ...] = (
            tuple(mission.allowed_domains),
            profile,
            real,
            headless,
            keep_open,
        )
        if self._browser_executor is None or self._browser_configuration != configuration:
            self.close()
            self._browser_executor = PlaywrightBrowserExecutor(
                mission.allowed_domains,
                credential_broker=EnvironmentCredentialBroker(),
                profile_directory=Path(profile),
                dry_run=not real,
                headless=headless,
                keep_open=keep_open,
            )
            self._browser_configuration = configuration
        return BrowserStepAdapter(self._browser_executor)(mission, step)

    def _desktop(self, mission: Mission, step: MissionStep) -> dict[str, object]:
        allowed_apps = tuple(
            item.strip() for item in os.getenv("AEP_DESKTOP_APPS", "").split(",") if item.strip()
        )
        allow_all = os.getenv("AEP_DESKTOP_ALLOW_ALL_APPS", "0") == "1"
        real = os.getenv("AEP_DESKTOP_REAL", "0") == "1"
        backend = AtSpiDesktopBackend() if real else DryRunDesktopBackend()
        executor = SafeDesktopExecutor(
            allowed_apps,
            backend,
            allow_all_applications=allow_all,
        )
        operation = DesktopOperation(step.action)
        action = DesktopAction(
            application=str(step.parameters.get("application", "")),
            operation=operation,
            control_name=str(step.parameters.get("control_name", "")),
            value=str(step.parameters.get("value", "")),
        )
        approval_granted = step.approval_status.value == "APPROVED" or not step.requires_approval
        return executor.execute(action, approval_granted=approval_granted)
