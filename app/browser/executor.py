"""Operador Playwright com allowlist, dry-run e corretor de credenciais."""

from __future__ import annotations

import atexit
from collections.abc import Iterable
from pathlib import Path
from threading import RLock
from typing import Any, Protocol
from urllib.parse import urlsplit

from app.browser.models import BrowserAction, BrowserOperation


class BrowserExecutionError(RuntimeError):
    pass


class CredentialBroker(Protocol):
    def get(self, reference: str) -> str: ...


class NullCredentialBroker:
    def get(self, reference: str) -> str:
        raise BrowserExecutionError(f"Credencial não disponível para a referência {reference!r}")


class EnvironmentCredentialBroker:
    """Resolve referência em variável local sem devolver o valor ao modelo ou log."""

    def __init__(self, prefix: str = "AEP_CREDENTIAL_") -> None:
        self.prefix = prefix

    def get(self, reference: str) -> str:
        import os

        safe_name = "".join(character if character.isalnum() else "_" for character in reference.upper())
        value = os.getenv(self.prefix + safe_name, "")
        if not value:
            raise BrowserExecutionError("Credencial não configurada no corretor local")
        return value


class PlaywrightBrowserExecutor:
    def __init__(
        self,
        allowed_domains: Iterable[str],
        credential_broker: CredentialBroker | None = None,
        profile_directory: str | Path | None = None,
        output_directory: str | Path = "var/aep",
        dry_run: bool = True,
        headless: bool = False,
        keep_open: bool = False,
    ) -> None:
        self.allowed_domains = tuple(item.lower().strip(".") for item in allowed_domains if item.strip("."))
        self.credential_broker = credential_broker or NullCredentialBroker()
        self.profile_directory = Path(profile_directory).expanduser() if profile_directory else None
        self.output_directory = Path(output_directory).expanduser().resolve()
        self.dry_run = dry_run
        self.headless = headless
        self.keep_open = keep_open
        self._session_lock = RLock()
        self._playwright_manager: Any | None = None
        self._context: Any | None = None
        self._browser: Any | None = None
        self._page: Any | None = None
        self._atexit_registered = False

    def execute(self, actions: list[BrowserAction], approval_granted: bool = False) -> dict[str, object]:
        self._validate(actions, approval_granted)
        if self.dry_run:
            return {
                "mode": "dry_run",
                "actions": [self._public_action(action) for action in actions],
                "completed": len(actions),
            }
        if self.keep_open:
            return self._execute_persistent(actions)
        return self._execute_temporary(actions)

    def close(self) -> None:
        """Encerra a sessão persistente, normalmente durante a parada do daemon."""

        with self._session_lock:
            context = self._context
            browser = self._browser
            manager = self._playwright_manager
            self._page = None
            self._context = None
            self._browser = None
            self._playwright_manager = None
            if context is not None:
                try:
                    context.close()
                except Exception:
                    pass
            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass
            if manager is not None:
                try:
                    manager.stop()
                except Exception:
                    pass

    def _validate(self, actions: list[BrowserAction], approval_granted: bool) -> None:
        if not actions:
            raise BrowserExecutionError("Plano de navegador vazio")
        for action in actions:
            if action.operation == BrowserOperation.NAVIGATE and not action.url:
                raise BrowserExecutionError("Navegação exige URL")
            if action.url:
                self._validate_url(action.url)
            if action.operation == BrowserOperation.FILL_CREDENTIAL and not action.credential_ref:
                raise BrowserExecutionError("Preenchimento de credencial exige uma referência")
            if action.operation == BrowserOperation.SUBMIT and not approval_granted:
                raise BrowserExecutionError("Envio final exige aprovação explícita")
            if action.operation in {
                BrowserOperation.CLICK,
                BrowserOperation.FILL,
                BrowserOperation.FILL_CREDENTIAL,
                BrowserOperation.SELECT,
                BrowserOperation.READ_TEXT,
                BrowserOperation.DOWNLOAD,
                BrowserOperation.SUBMIT,
            } and not action.selector:
                raise BrowserExecutionError(f"A operação {action.operation} exige seletor")
            if action.operation == BrowserOperation.SCREENSHOT:
                self._safe_output_path(action.value, "evidence/browser.png")
            if action.operation == BrowserOperation.DOWNLOAD:
                self._safe_output_path(action.value, "downloads")

    def _validate_url(self, value: str) -> None:
        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise BrowserExecutionError("Somente URLs HTTPS sem credenciais embutidas são permitidas")
        domain = parsed.hostname.lower()
        if not any(domain == allowed or domain.endswith("." + allowed) for allowed in self.allowed_domains):
            raise BrowserExecutionError(f"Domínio não permitido: {domain}")

    def _safe_output_path(self, value: str, default_relative: str) -> Path:
        relative = Path(value or default_relative)
        if relative.is_absolute() or ".." in relative.parts:
            raise BrowserExecutionError("Caminho de saída fora do diretório operacional")
        resolved = (self.output_directory / relative).resolve()
        try:
            resolved.relative_to(self.output_directory)
        except ValueError as exc:
            raise BrowserExecutionError("Caminho de saída fora do diretório operacional") from exc
        return resolved

    @staticmethod
    def _public_action(action: BrowserAction) -> dict[str, object]:
        return {
            "operation": action.operation.value,
            "url": action.url,
            "selector": action.selector,
            "value_present": bool(action.value),
            "credential_reference": action.credential_ref or None,
        }

    @staticmethod
    def _load_sync_playwright():
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BrowserExecutionError(
                "Playwright não instalado. Use requirements-executive.txt e execute playwright install chromium."
            ) from exc
        return sync_playwright

    def _execute_temporary(self, actions: list[BrowserAction]) -> dict[str, object]:
        sync_playwright = self._load_sync_playwright()
        outputs: list[dict[str, object]] = []
        with sync_playwright() as playwright:
            launch_args = {"headless": self.headless}
            if self.profile_directory:
                self.profile_directory.mkdir(parents=True, exist_ok=True)
                context = playwright.chromium.launch_persistent_context(str(self.profile_directory), **launch_args)
                browser = None
            else:
                browser = playwright.chromium.launch(**launch_args)
                context = browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            try:
                for action in actions:
                    outputs.append(self._execute_action(page, action))
            finally:
                context.close()
                if browser is not None:
                    browser.close()
        return {"mode": "real", "completed": len(outputs), "outputs": outputs}

    def _execute_persistent(self, actions: list[BrowserAction]) -> dict[str, object]:
        with self._session_lock:
            page = self._ensure_persistent_page()
            outputs = [self._execute_action(page, action) for action in actions]
            return {
                "mode": "real",
                "session": "persistent",
                "completed": len(outputs),
                "outputs": outputs,
            }

    def _ensure_persistent_page(self):  # type: ignore[no-untyped-def]
        if self._page is not None and not self._page.is_closed():
            return self._page

        self.close()
        sync_playwright = self._load_sync_playwright()
        manager = sync_playwright().start()
        launch_args = {"headless": self.headless}
        try:
            if self.profile_directory:
                self.profile_directory.mkdir(parents=True, exist_ok=True)
                context = manager.chromium.launch_persistent_context(
                    str(self.profile_directory),
                    **launch_args,
                )
                browser = None
            else:
                browser = manager.chromium.launch(**launch_args)
                context = browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
        except Exception:
            try:
                manager.stop()
            except Exception:
                pass
            raise

        self._playwright_manager = manager
        self._browser = browser
        self._context = context
        self._page = page
        if not self._atexit_registered:
            atexit.register(self.close)
            self._atexit_registered = True
        return page

    def _execute_action(self, page, action: BrowserAction) -> dict[str, object]:  # type: ignore[no-untyped-def]
        operation = action.operation
        if operation == BrowserOperation.NAVIGATE:
            page.goto(action.url, wait_until="domcontentloaded")
            return {"operation": operation, "url": page.url}
        locator = page.locator(action.selector)
        if operation == BrowserOperation.READ_TEXT:
            return {"operation": operation, "text": locator.inner_text()[:4000]}
        if operation == BrowserOperation.CLICK:
            locator.click()
        elif operation == BrowserOperation.FILL:
            locator.fill(action.value)
        elif operation == BrowserOperation.FILL_CREDENTIAL:
            secret = self.credential_broker.get(action.credential_ref)
            locator.fill(secret)
            del secret
        elif operation == BrowserOperation.SELECT:
            locator.select_option(action.value)
        elif operation == BrowserOperation.SCREENSHOT:
            output = self._safe_output_path(action.value, "evidence/browser.png")
            output.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(output), full_page=bool(action.options.get("full_page", True)))
            return {"operation": operation, "path": str(output)}
        elif operation == BrowserOperation.DOWNLOAD:
            with page.expect_download() as download_info:
                locator.click()
            download = download_info.value
            directory = self._safe_output_path(action.value, "downloads")
            directory.mkdir(parents=True, exist_ok=True)
            output = directory / Path(download.suggested_filename).name
            download.save_as(str(output))
            return {"operation": operation, "path": str(output)}
        elif operation == BrowserOperation.SUBMIT:
            locator.click()
        else:
            raise BrowserExecutionError(f"Operação não implementada: {operation}")
        return {"operation": operation, "ok": True}
