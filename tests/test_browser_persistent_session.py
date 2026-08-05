from __future__ import annotations

import sys
from types import ModuleType

from app.browser.executor import PlaywrightBrowserExecutor
from app.browser.models import BrowserAction, BrowserOperation


class FakePage:
    def __init__(self) -> None:
        self.url = "about:blank"
        self.closed = False
        self.visited: list[str] = []

    def is_closed(self) -> bool:
        return self.closed

    def goto(self, url: str, wait_until: str) -> None:
        assert wait_until == "domcontentloaded"
        self.url = url
        self.visited.append(url)


class FakeContext:
    def __init__(self) -> None:
        self.page = FakePage()
        self.pages = [self.page]
        self.close_count = 0

    def new_page(self) -> FakePage:
        return self.page

    def close(self) -> None:
        self.close_count += 1
        self.page.closed = True


class FakeChromium:
    def __init__(self, context: FakeContext) -> None:
        self.context = context
        self.launch_count = 0

    def launch_persistent_context(self, profile: str, **kwargs):  # type: ignore[no-untyped-def]
        assert profile
        assert kwargs == {"headless": False}
        self.launch_count += 1
        return self.context


class FakeManager:
    def __init__(self, context: FakeContext) -> None:
        self.chromium = FakeChromium(context)
        self.stop_count = 0

    def stop(self) -> None:
        self.stop_count += 1


class FakePlaywrightFactory:
    def __init__(self, manager: FakeManager) -> None:
        self.manager = manager
        self.start_count = 0

    def start(self) -> FakeManager:
        self.start_count += 1
        return self.manager


def test_browser_session_remains_open_between_missions(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    context = FakeContext()
    manager = FakeManager(context)
    factory = FakePlaywrightFactory(manager)

    package = ModuleType("playwright")
    sync_api = ModuleType("playwright.sync_api")
    sync_api.sync_playwright = lambda: factory  # type: ignore[attr-defined]
    package.sync_api = sync_api  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "playwright", package)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", sync_api)

    executor = PlaywrightBrowserExecutor(
        ["example.com"],
        profile_directory=tmp_path / "profile",
        dry_run=False,
        headless=False,
        keep_open=True,
    )

    first = executor.execute(
        [BrowserAction(BrowserOperation.NAVIGATE, url="https://example.com/")]
    )
    second = executor.execute(
        [BrowserAction(BrowserOperation.NAVIGATE, url="https://example.com/second")]
    )

    assert first["session"] == "persistent"
    assert second["session"] == "persistent"
    assert manager.chromium.launch_count == 1
    assert factory.start_count == 1
    assert context.close_count == 0
    assert context.page.visited == ["https://example.com/", "https://example.com/second"]

    executor.close()

    assert context.close_count == 1
    assert manager.stop_count == 1
