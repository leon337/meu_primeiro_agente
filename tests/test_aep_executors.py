from pathlib import Path

import pytest

from app.browser.executor import BrowserExecutionError, PlaywrightBrowserExecutor
from app.browser.models import BrowserAction, BrowserOperation
from app.desktop.executor import DesktopAction, DesktopExecutionError, DesktopOperation, SafeDesktopExecutor
from app.voice.commands import VoiceIntent, parse_voice_command


def test_browser_dry_run_respects_allowlist_and_hides_values(tmp_path: Path) -> None:
    executor = PlaywrightBrowserExecutor(("vercel.com",), output_directory=tmp_path, dry_run=True)
    result = executor.execute([
        BrowserAction(BrowserOperation.NAVIGATE, url="https://vercel.com/dashboard"),
        BrowserAction(BrowserOperation.FILL, selector="#name", value="valor privado"),
    ])
    assert result["mode"] == "dry_run"
    assert result["actions"][1]["value_present"] is True
    assert "valor privado" not in str(result)


def test_browser_blocks_domain_plain_http_and_unapproved_submit(tmp_path: Path) -> None:
    executor = PlaywrightBrowserExecutor(("vercel.com",), output_directory=tmp_path, dry_run=True)
    with pytest.raises(BrowserExecutionError, match="HTTPS"):
        executor.execute([BrowserAction(BrowserOperation.NAVIGATE, url="http://vercel.com")])
    with pytest.raises(BrowserExecutionError, match="Domínio"):
        executor.execute([BrowserAction(BrowserOperation.NAVIGATE, url="https://example.com")])
    with pytest.raises(BrowserExecutionError, match="aprovação"):
        executor.execute([BrowserAction(BrowserOperation.SUBMIT, selector="button")])


def test_browser_requires_targets_and_confines_outputs(tmp_path: Path) -> None:
    executor = PlaywrightBrowserExecutor(("vercel.com",), output_directory=tmp_path, dry_run=True)
    with pytest.raises(BrowserExecutionError, match="URL"):
        executor.execute([BrowserAction(BrowserOperation.NAVIGATE)])
    with pytest.raises(BrowserExecutionError, match="seletor"):
        executor.execute([BrowserAction(BrowserOperation.DOWNLOAD)], approval_granted=True)
    with pytest.raises(BrowserExecutionError, match="diretório operacional"):
        executor.execute([BrowserAction(BrowserOperation.SCREENSHOT, value="../../fora.png")])
    with pytest.raises(BrowserExecutionError, match="diretório operacional"):
        executor.execute([BrowserAction(BrowserOperation.SCREENSHOT, value="/tmp/fora.png")])


def test_desktop_is_allowlisted_and_mutations_need_approval() -> None:
    executor = SafeDesktopExecutor(("Brave",))
    assert executor.execute(DesktopAction("Brave", DesktopOperation.FOCUS_APPLICATION))["mode"] == "dry_run"
    with pytest.raises(DesktopExecutionError, match="lista"):
        executor.execute(DesktopAction("Terminal", DesktopOperation.FOCUS_APPLICATION))
    with pytest.raises(DesktopExecutionError, match="aprovação"):
        executor.execute(DesktopAction("Brave", DesktopOperation.CLICK_NAMED_CONTROL, "Entrar"))


def test_voice_commands_do_not_execute_implicitly() -> None:
    assert parse_voice_command("status da missão MCF-1").intent == VoiceIntent.STATUS
    assert parse_voice_command("parar missão MCF-1").intent == VoiceIntent.STOP
    assert parse_voice_command("abra o GitHub").intent == VoiceIntent.CHAT
