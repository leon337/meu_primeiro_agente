"""Controle de aplicativos gráficos por registro, acessibilidade e foco de janela."""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
import shutil
import subprocess
from time import monotonic, sleep
from typing import Protocol


class DesktopOperation(StrEnum):
    LIST_APPLICATIONS = "list_applications"
    LAUNCH_APPLICATION = "launch_application"
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


@dataclass(frozen=True, slots=True)
class DesktopApplication:
    name: str
    desktop_id: str
    path: Path


class DesktopExecutionError(RuntimeError):
    pass


class DesktopBackend(Protocol):
    def execute(self, action: DesktopAction) -> dict[str, object]: ...


class DesktopApplicationRegistry:
    """Descobre e inicia aplicativos registrados por arquivos ``.desktop``.

    Não interpreta comandos arbitrários e não usa shell. A execução é delegada ao
    ``gtk-launch`` ou ao ``gio launch`` com argumentos separados.
    """

    def __init__(self, search_paths: tuple[Path, ...] | None = None) -> None:
        self.search_paths = search_paths or (
            Path.home() / ".local/share/applications",
            Path("/usr/local/share/applications"),
            Path("/usr/share/applications"),
        )

    def applications(self) -> tuple[DesktopApplication, ...]:
        discovered: dict[str, DesktopApplication] = {}
        for directory in self.search_paths:
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.desktop")):
                application = self._read(path)
                if application is not None:
                    discovered.setdefault(application.desktop_id.casefold(), application)
        return tuple(sorted(discovered.values(), key=lambda item: item.name.casefold()))

    def list_public(self, limit: int = 500) -> list[dict[str, str]]:
        return [
            {"name": item.name, "desktop_id": item.desktop_id}
            for item in self.applications()[: max(1, min(limit, 1000))]
        ]

    def resolve(self, query: str) -> DesktopApplication:
        normalized = query.strip().casefold()
        if not normalized:
            raise DesktopExecutionError("Nome ou identificador do aplicativo é obrigatório")
        applications = self.applications()
        exact = [
            item
            for item in applications
            if normalized in {item.name.casefold(), item.desktop_id.casefold()}
        ]
        if exact:
            return exact[0]
        partial = [
            item
            for item in applications
            if normalized in item.name.casefold() or normalized in item.desktop_id.casefold()
        ]
        if not partial:
            raise DesktopExecutionError(f"Aplicativo registrado não encontrado: {query}")
        partial.sort(key=lambda item: (len(item.name), item.name.casefold()))
        return partial[0]

    def launch(self, query: str) -> dict[str, object]:
        application = self.resolve(query)
        gtk_launch = shutil.which("gtk-launch")
        gio = shutil.which("gio")
        if gtk_launch:
            command = [gtk_launch, application.desktop_id]
        elif gio:
            command = [gio, "launch", str(application.path)]
        else:
            raise DesktopExecutionError("gtk-launch ou gio não está disponível no sistema")
        try:
            process = subprocess.Popen(  # noqa: S603 - executável resolvido sem shell
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as exc:
            raise DesktopExecutionError(f"Não foi possível iniciar {application.name}") from exc
        return {
            "launched": True,
            "application": application.name,
            "desktop_id": application.desktop_id,
            "pid": process.pid,
        }

    @staticmethod
    def _read(path: Path) -> DesktopApplication | None:
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            parser.read(path, encoding="utf-8")
            entry = parser["Desktop Entry"]
        except (OSError, KeyError, configparser.Error, UnicodeError):
            return None
        if entry.get("Type", "Application") != "Application":
            return None
        if entry.getboolean("Hidden", fallback=False):
            return None
        name = entry.get("Name", "").strip() or path.stem
        return DesktopApplication(name=name, desktop_id=path.stem, path=path)


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
    """Backend Linux com lançamento genérico e acessibilidade quando disponível."""

    def __init__(
        self,
        max_nodes: int = 5000,
        registry: DesktopApplicationRegistry | None = None,
        launch_wait_seconds: float = 8.0,
    ) -> None:
        self.max_nodes = max_nodes
        self.registry = registry or DesktopApplicationRegistry()
        self.launch_wait_seconds = max(0.0, launch_wait_seconds)
        try:
            import pyatspi  # type: ignore[import-not-found]
        except ImportError:
            self.pyatspi = None
        else:
            self.pyatspi = pyatspi

    def execute(self, action: DesktopAction) -> dict[str, object]:
        if action.operation == DesktopOperation.LIST_APPLICATIONS:
            applications = self.registry.list_public()
            return {"applications": applications, "count": len(applications)}
        if action.operation == DesktopOperation.LAUNCH_APPLICATION:
            result = self.registry.launch(action.application)
            deadline = monotonic() + self.launch_wait_seconds
            while monotonic() < deadline:
                if self._try_focus(action.application):
                    result["focused"] = True
                    return result
                sleep(0.25)
            result["focused"] = False
            return result
        if action.operation == DesktopOperation.FOCUS_APPLICATION:
            if self._try_focus(action.application):
                return {"focused": True, "application": action.application}
            raise DesktopExecutionError(f"Não foi possível localizar ou focar: {action.application}")

        app = self._find_application(action.application)
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

    def _try_focus(self, name: str) -> bool:
        if self.pyatspi is not None:
            try:
                application = self._find_application(name)
                application.queryComponent().grabFocus()
                return True
            except Exception:
                pass
        return self._focus_external_window(name)

    @staticmethod
    def _focus_external_window(name: str) -> bool:
        candidates = (
            ([shutil.which("wmctrl"), "-xa", name],),
            ([shutil.which("xdotool"), "search", "--name", name, "windowactivate", "--sync"],),
        )
        for wrapped in candidates:
            command = wrapped[0]
            if command[0] is None:
                continue
            try:
                completed = subprocess.run(  # noqa: S603 - executável resolvido sem shell
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired):
                continue
            if completed.returncode == 0:
                return True
        return False

    def _find_application(self, name: str):  # type: ignore[no-untyped-def]
        if self.pyatspi is None:
            raise DesktopExecutionError("Bindings pyatspi não estão instalados no sistema")
        normalized = name.casefold().strip()
        desktop = self.pyatspi.Registry.getDesktop(0)
        applications = list(desktop)
        for app in applications:
            if getattr(app, "name", "").casefold() == normalized:
                return app
        for app in applications:
            app_name = getattr(app, "name", "").casefold()
            if normalized and (normalized in app_name or app_name in normalized):
                return app
        raise DesktopExecutionError(f"Aplicativo não encontrado: {name}")

    def _find_named(self, root, name: str):  # type: ignore[no-untyped-def]
        queue = [root]
        visited = 0
        normalized = name.casefold()
        while queue:
            node = queue.pop(0)
            visited += 1
            if visited > self.max_nodes:
                break
            if getattr(node, "name", "").casefold() == normalized:
                return node
            try:
                queue.extend(node)
            except Exception:
                continue
        raise DesktopExecutionError(f"Controle não encontrado: {name}")


class SafeDesktopExecutor:
    def __init__(
        self,
        allowed_applications: tuple[str, ...],
        backend: DesktopBackend | None = None,
        allow_all_applications: bool = False,
    ) -> None:
        self.allowed_applications = tuple(item.casefold() for item in allowed_applications)
        self.backend = backend or DryRunDesktopBackend()
        self.allow_all_applications = allow_all_applications

    def execute(self, action: DesktopAction, approval_granted: bool = False) -> dict[str, object]:
        if action.operation != DesktopOperation.LIST_APPLICATIONS:
            if not action.application.strip():
                raise DesktopExecutionError("Aplicativo é obrigatório")
            if not self.allow_all_applications and action.application.casefold() not in self.allowed_applications:
                raise DesktopExecutionError("Aplicativo fora da lista permitida")
        if action.operation in {DesktopOperation.CLICK_NAMED_CONTROL, DesktopOperation.SET_NAMED_TEXT}:
            if not approval_granted:
                raise DesktopExecutionError("Ação de alteração no desktop exige aprovação")
        if action.operation in {
            DesktopOperation.CLICK_NAMED_CONTROL,
            DesktopOperation.SET_NAMED_TEXT,
            DesktopOperation.READ_NAMED_TEXT,
        } and not action.control_name:
            raise DesktopExecutionError("Nome acessível do controle é obrigatório")
        return self.backend.execute(action)
