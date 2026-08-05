"""Controle de desktop por acessibilidade, sem shell nem coordenadas livres."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class DesktopOperation(StrEnum):
    FOCUS_APPLICATION = "focus_application"
    CLICK_NAMED_CONTROL = "click_named_control"
    SET_NAMED_TEXT = "set_named_text"
    READ_NAMED_TEXT = "read_named_text"


@dataclass(frozen=True, slots=True)
class DesktopAction:
    application: str
    operation: DesktopOperation
    control_name: str = ""
    value: str = ""


class DesktopExecutionError(RuntimeError):
    pass


class DesktopBackend(Protocol):
    def execute(self, action: DesktopAction) -> dict[str, object]: ...


class DryRunDesktopBackend:
    def execute(self, action: DesktopAction) -> dict[str, object]:
        return {
            "mode": "dry_run",
            "application": action.application,
            "operation": action.operation.value,
            "control_name": action.control_name,
            "value_present": bool(action.value),
        }


class AtSpiDesktopBackend:
    """Backend opcional. Requer bindings AT-SPI do sistema Linux."""

    def __init__(self, max_nodes: int = 5000) -> None:
        self.max_nodes = max_nodes
        try:
            import pyatspi  # type: ignore[import-not-found]
        except ImportError as exc:
            raise DesktopExecutionError("Bindings pyatspi não estão instalados no sistema") from exc
        self.pyatspi = pyatspi

    def execute(self, action: DesktopAction) -> dict[str, object]:
        app = self._find_application(action.application)
        if action.operation == DesktopOperation.FOCUS_APPLICATION:
            component = app.queryComponent()
            component.grabFocus()
            return {"focused": True, "application": action.application}
        target = self._find_named(app, action.control_name)
        if action.operation == DesktopOperation.CLICK_NAMED_CONTROL:
            action_iface = target.queryAction()
            for index in range(action_iface.nActions):
                if action_iface.getName(index).lower() in {"click", "press", "activate"}:
                    action_iface.doAction(index)
                    return {"clicked": True, "control": action.control_name}
            raise DesktopExecutionError("Controle não expõe ação segura de clique")
        if action.operation == DesktopOperation.SET_NAMED_TEXT:
            editable = target.queryEditableText()
            editable.setTextContents(action.value)
            return {"filled": True, "control": action.control_name}
        if action.operation == DesktopOperation.READ_NAMED_TEXT:
            text = target.queryText()
            return {"text": text.getText(0, text.characterCount)[:4000], "control": action.control_name}
        raise DesktopExecutionError("Operação de desktop não implementada")

    def _find_application(self, name: str):  # type: ignore[no-untyped-def]
        desktop = self.pyatspi.Registry.getDesktop(0)
        for app in desktop:
            if getattr(app, "name", "").casefold() == name.casefold():
                return app
        raise DesktopExecutionError(f"Aplicativo não encontrado: {name}")

    def _find_named(self, root, name: str):  # type: ignore[no-untyped-def]
        queue = [root]
        visited = 0
        while queue:
            node = queue.pop(0)
            visited += 1
            if visited > self.max_nodes:
                break
            if getattr(node, "name", "").casefold() == name.casefold():
                return node
            try:
                queue.extend(node)
            except Exception:
                continue
        raise DesktopExecutionError(f"Controle não encontrado: {name}")


class SafeDesktopExecutor:
    def __init__(self, allowed_applications: tuple[str, ...], backend: DesktopBackend | None = None) -> None:
        self.allowed_applications = tuple(item.casefold() for item in allowed_applications)
        self.backend = backend or DryRunDesktopBackend()

    def execute(self, action: DesktopAction, approval_granted: bool = False) -> dict[str, object]:
        if action.application.casefold() not in self.allowed_applications:
            raise DesktopExecutionError("Aplicativo fora da lista permitida")
        if action.operation in {DesktopOperation.CLICK_NAMED_CONTROL, DesktopOperation.SET_NAMED_TEXT} and not approval_granted:
            raise DesktopExecutionError("Ação de alteração no desktop exige aprovação")
        if action.operation != DesktopOperation.FOCUS_APPLICATION and not action.control_name:
            raise DesktopExecutionError("Nome acessível do controle é obrigatório")
        return self.backend.execute(action)
