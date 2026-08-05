from __future__ import annotations

from pathlib import Path

import pytest

from app.desktop.executor import (
    DesktopAction,
    DesktopApplicationRegistry,
    DesktopExecutionError,
    DesktopOperation,
    SafeDesktopExecutor,
)


class RecordingBackend:
    def __init__(self) -> None:
        self.actions: list[DesktopAction] = []

    def execute(self, action: DesktopAction) -> dict[str, object]:
        self.actions.append(action)
        return {"operation": action.operation.value, "application": action.application}


def test_allow_all_mode_accepts_any_registered_application_name() -> None:
    backend = RecordingBackend()
    executor = SafeDesktopExecutor((), backend, allow_all_applications=True)

    result = executor.execute(
        DesktopAction("Brave", DesktopOperation.LAUNCH_APPLICATION),
    )

    assert result == {"operation": "launch_application", "application": "Brave"}
    assert backend.actions[0].application == "Brave"


def test_allowlist_mode_rejects_unknown_application() -> None:
    executor = SafeDesktopExecutor(("Visual Studio Code",), RecordingBackend())

    with pytest.raises(DesktopExecutionError, match="fora da lista"):
        executor.execute(DesktopAction("Brave", DesktopOperation.FOCUS_APPLICATION))


def test_listing_applications_does_not_require_an_application_name() -> None:
    backend = RecordingBackend()
    executor = SafeDesktopExecutor((), backend)

    result = executor.execute(DesktopAction("", DesktopOperation.LIST_APPLICATIONS))

    assert result["operation"] == "list_applications"


def test_mutating_accessibility_action_still_requires_approval() -> None:
    executor = SafeDesktopExecutor((), RecordingBackend(), allow_all_applications=True)

    with pytest.raises(DesktopExecutionError, match="exige aprovação"):
        executor.execute(
            DesktopAction(
                "Editor",
                DesktopOperation.SET_NAMED_TEXT,
                control_name="Documento",
                value="texto",
            )
        )


def test_registry_discovers_and_resolves_desktop_entries(tmp_path: Path) -> None:
    entry = tmp_path / "brave-browser.desktop"
    entry.write_text(
        "[Desktop Entry]\nType=Application\nName=Brave Web Browser\nExec=brave-browser %U\n",
        encoding="utf-8",
    )
    registry = DesktopApplicationRegistry((tmp_path,))

    application = registry.resolve("Brave")

    assert application.name == "Brave Web Browser"
    assert application.desktop_id == "brave-browser"
