"""Tests for the DoubloonApp core behavior."""

# ruff: noqa: ANN401, EM101
# pyright: reportPrivateUsage=none
# pylint: disable=redefined-outer-name
# pylint: disable=missing-param-doc
# pylint: disable=missing-return-doc
# pylint: disable=missing-raises-doc
# pylint: disable=E1101

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast
from unittest.mock import AsyncMock, MagicMock, create_autospec

import pytest
from textual.css.query import NoMatches
from textual.widgets import LoadingIndicator

from appui.doubloon_app import DoubloonApp
from appui.doubloon_config import DoubloonConfig
from appui.enums import LoggingLevel, TimeFormat
from appui.messages import AppExit
from calahan import YFinance

_PathOpenCallable = Callable[..., TextIO | BinaryIO]


def dummy_worker(*, is_running: bool = False, is_cancelled: bool = False) -> MagicMock:
    """Create a Worker mock with the given state."""

    return create_autospec(
        "Worker",
        is_running=is_running,
        is_cancelled=is_cancelled,
        cancel=MagicMock(),
    )


@pytest.fixture
def yfinance_stub() -> YFinance:
    """Provide a YFinance stub wired into the app constructor."""

    return create_autospec(YFinance, prime=AsyncMock(), aclose=AsyncMock())


@pytest.fixture
def app(yfinance_stub: YFinance) -> DoubloonApp:
    """Create a fresh app instance for each test."""

    app = DoubloonApp()
    app._yfinance = yfinance_stub
    return app


def test_compose_emits_loading_indicator_and_footer(app: DoubloonApp) -> None:
    """Verify compose yields only the loading indicator and footer."""

    nodes = list(app.compose())

    num_elements = 2  # LoadingIndicator + Footer

    assert len(nodes) == num_elements
    assert isinstance(nodes[0], LoadingIndicator)
    assert nodes[1] is app._footer


def test_accessors_expose_internal_instances(
    app: DoubloonApp, yfinance_stub: MagicMock
) -> None:
    """config/yfinance properties should proxy the private attributes."""

    assert app.config is app._config
    assert app.yfinance is yfinance_stub


def test_on_mount_sets_worker_title_and_screen(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mount should kick off priming, set title, and install watchlist."""

    app = DoubloonApp()
    worker = object()
    prime_spy = MagicMock(return_value=worker)
    monkeypatch.setattr(app, "_prime_yfinance", prime_spy)

    install_spy = MagicMock()
    monkeypatch.setattr(app, "install_screen", install_spy)
    sentinel_screen = object()
    monkeypatch.setattr("appui.doubloon_app.WatchlistScreen", lambda: sentinel_screen)

    app.on_mount()

    assert app._priming_worker is worker
    assert app.title == app.config.title
    install_spy.assert_called_once()
    args, kwargs = install_spy.call_args
    assert args[0] is sentinel_screen
    assert kwargs["name"] == "watchlist"


@pytest.mark.parametrize(
    ("worker_state", "cancel_call_count"),
    [
        pytest.param(True, 1),
        pytest.param(False, 0),
    ],
)
def test_on_unmount_cancels_worker_if_running(
    app: DoubloonApp, *, worker_state: bool, cancel_call_count: int
) -> None:
    """Running priming workers should be cancelled on unmount."""

    worker = dummy_worker(is_running=worker_state)
    app._priming_worker = worker

    app.on_unmount()

    assert worker.cancel.call_count == cancel_call_count


@pytest.mark.asyncio
async def test_action_quit_posts_app_exit(app: DoubloonApp) -> None:
    """Ensure quit action posts the AppExit message."""

    post_spy = MagicMock()
    app.post_message = post_spy

    await app.action_quit()

    post_spy.assert_called_once()
    message = post_spy.call_args.args[0]
    assert isinstance(message, AppExit)


@pytest.mark.asyncio
async def test_on_app_exit_cleans_up_resources(
    app: DoubloonApp,
    yfinance_stub: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """App exit should cancel work, close yfinance, and exit."""

    worker = dummy_worker(is_running=True)
    app._priming_worker = worker
    exit_spy = MagicMock()
    monkeypatch.setattr(app, "exit", exit_spy)

    await app.on_app_exit(MagicMock())

    worker.cancel.assert_called_once()
    yfinance_stub.aclose.assert_awaited_once()
    exit_spy.assert_called_once_with()


@pytest.mark.asyncio
async def test_on_app_exit_logs_aclose_failures(
    app: DoubloonApp,
    yfinance_stub: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Failure to close YFinance should be logged."""

    yfinance_stub.aclose.side_effect = RuntimeError("boom")
    exit_spy = MagicMock()
    monkeypatch.setattr(app, "exit", exit_spy)

    with caplog.at_level(logging.ERROR):
        await app.on_app_exit(MagicMock())

    assert "Error closing YFinance" in caplog.text
    exit_spy.assert_called_once()


def test_exit_blocked_until_cleanup_allows_it(app: DoubloonApp) -> None:
    """Direct exit calls should be rejected until cleanup flips the guard."""

    with pytest.raises(RuntimeError):
        app.exit()


def test_exit_delegates_to_super_when_allowed(
    app: DoubloonApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Once _may_exit is set the call should reach App.exit."""

    calls: list[tuple[Any, Any, int, Any]] = []

    def fake_super_exit(
        self: DoubloonApp, result: Any, return_code: int, message: Any
    ) -> None:
        calls.append((self, result, return_code, message))

    monkeypatch.setattr("textual.app.App.exit", fake_super_exit)

    app._may_exit = True
    app.exit(message="Done", return_code=5)

    assert app._may_exit is False
    assert calls == [(app, None, 5, "Done")]


def test_load_config_returns_when_already_loaded(
    app: DoubloonApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No file IO should occur once configuration is loaded."""

    loaded = DoubloonConfig(title="Loaded")
    app._config_loaded = True
    app._config = loaded

    def fail_open(*_: object, **__: object) -> None:
        msg = "load_config should not open a file when already loaded"
        raise AssertionError(msg)

    monkeypatch.setattr("appui.doubloon_app.Path.open", fail_open)

    app.load_config("unused.json")

    assert app.config is loaded


def test_load_config_reads_json_payload(app: DoubloonApp, tmp_path: Path) -> None:
    """Valid JSON payloads should hydrate the model."""

    payload = {
        "title": "Configured",
        "log_level": "warning",
        "time_format": "12h",
        "watchlist": {"quotes": ["SPY"]},
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    app.load_config(str(path))

    assert app.config.title == "Configured"
    assert app.config.log_level == logging.WARNING
    assert app.config.time_format is TimeFormat.TWELVE_HOUR
    assert app._config_loaded is True


def test_load_config_handles_missing_file(
    app: DoubloonApp, caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    """Missing files should log a warning and fall back to defaults."""

    missing = tmp_path / "missing.json"

    with caplog.at_level(logging.WARNING):
        app.load_config(str(missing))

    assert "Config file not found" in caplog.text
    default = DoubloonConfig()
    assert app.config.title == default.title
    assert app._config_loaded is True


def test_load_config_handles_empty_file(
    app: DoubloonApp, caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    """Empty config files should be reported and replaced with defaults."""

    path = tmp_path / "empty.json"
    path.write_text("", encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        app.load_config(str(path))

    assert "Config file is empty" in caplog.text
    assert app.config.title == DoubloonConfig().title
    assert app._config_loaded is True


def test_load_config_handles_invalid_json(
    app: DoubloonApp, caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    """Invalid JSON should log an exception and revert to defaults."""

    path = tmp_path / "bad.json"
    path.write_text("{invalid", encoding="utf-8")

    with caplog.at_level(logging.ERROR):
        app.load_config(str(path))

    assert "error decoding JSON file" in caplog.text
    assert app.config.title == DoubloonConfig().title
    assert app._config_loaded is True


def test_save_config_writes_model_dump(app: DoubloonApp, tmp_path: Path) -> None:
    """save_config should persist the config model as JSON."""

    app._config = DoubloonConfig(
        title="Saved",
        log_level=LoggingLevel.DEBUG,
        time_format=TimeFormat.TWELVE_HOUR,
    )
    path = tmp_path / "saved.json"

    app.save_config(str(path))

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == app.config.model_dump(mode="json")


def test_save_config_logs_missing_parent(
    app: DoubloonApp, caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    """Attempting to save into a missing directory should log an exception."""

    path = tmp_path / "missing" / "saved.json"

    with caplog.at_level(logging.ERROR):
        app.save_config(str(path))

    assert "Config file not found" in caplog.text


def test_save_config_logs_permission_error(
    app: DoubloonApp,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Permission errors should be surfaced via logging."""

    original_open = cast("_PathOpenCallable", Path.open)
    target = tmp_path / "saved.json"

    def fake_open(self: Path, *args: Any, **kwargs: Any) -> TextIO | BinaryIO:
        if self == target:
            raise PermissionError("denied")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr("appui.doubloon_app.Path.open", fake_open)

    with caplog.at_level(logging.ERROR):
        app.save_config(str(target))

    assert "Permission denied" in caplog.text


def test_save_config_uses_canonical_when_path_missing(
    app: DoubloonApp, tmp_path: Path
) -> None:
    """Calling save_config() with None should use the canonical path."""

    target = tmp_path / "saved.json"
    app._config_path = str(target)
    app._config = DoubloonConfig(title="Canonical")

    app.save_config()

    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["title"] == "Canonical"
    assert app._config_path == str(target)


def test_save_config_warns_without_path(
    app: DoubloonApp, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Calling save_config() with no canonical path should log and skip."""

    app._config_path = None
    opened: list[Path] = []
    original_open = cast("_PathOpenCallable", Path.open)

    def fail_open(self: Path, *args: Any, **kwargs: Any) -> TextIO | BinaryIO:
        opened.append(self)
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr("appui.doubloon_app.Path.open", fail_open)

    with caplog.at_level(logging.WARNING):
        app.save_config()

    assert "Config path not set" in caplog.text
    assert not opened


@pytest.mark.asyncio
async def test_persist_config_invokes_save_config(
    app: DoubloonApp, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """persist_config should delegate to save_config using the configured path."""

    target = str(tmp_path / "config.json")
    app._config_path = target
    app.save_config = MagicMock()

    calls: list[tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]] = []

    async def fake_to_thread(  # noqa: RUF029 Used as a synchronous function below
        func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> None:
        calls.append((func, args, kwargs))
        func(*args, **kwargs)

    monkeypatch.setattr("appui.doubloon_app.asyncio.to_thread", fake_to_thread)

    await DoubloonApp.persist_config.__wrapped__(app)  # type: ignore[attr-defined]

    app.save_config.assert_called_once_with()
    assert calls == [(app.save_config, (), {})]
    assert app._config_path == target


@pytest.mark.asyncio
async def test_prime_yfinance_triggers_finish_when_worker_pending(
    app: DoubloonApp,
    yfinance_stub: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_prime_yfinance should await prime and finish loading when active."""

    worker = dummy_worker(is_running=True, is_cancelled=False)
    app._priming_worker = worker
    finish_spy = MagicMock()
    monkeypatch.setattr(app, "_finish_loading", finish_spy)

    await DoubloonApp._prime_yfinance.__wrapped__(app)  # type: ignore[attr-defined]

    yfinance_stub.prime.assert_awaited_once()
    finish_spy.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "worker_state",
    [
        pytest.param(None, id="worker-missing"),
        pytest.param(
            dummy_worker(is_running=True, is_cancelled=True), id="worker-cancelled"
        ),
    ],
)
async def test_prime_yfinance_skips_finish_when_cancelled(
    worker_state: MagicMock | None,
    app: DoubloonApp,
    yfinance_stub: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_prime_yfinance should not call _finish_loading when cancelled."""

    app._priming_worker = worker_state
    finish_spy = MagicMock()
    monkeypatch.setattr(app, "_finish_loading", finish_spy)

    await DoubloonApp._prime_yfinance.__wrapped__(app)  # type: ignore[attr-defined]

    yfinance_stub.prime.assert_awaited_once()
    finish_spy.assert_not_called()


def test_finish_loading_removes_indicator_and_pushes_screen(
    app: DoubloonApp,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_finish_loading should remove the indicator and push the watchlist."""

    indicator = MagicMock()
    query_spy = MagicMock(return_value=indicator)
    monkeypatch.setattr(app, "query_one", query_spy)
    push_spy = MagicMock()
    monkeypatch.setattr(app, "push_screen", push_spy)
    app._priming_worker = dummy_worker(is_running=False)

    app._finish_loading()

    query_spy.assert_called_once()
    indicator.remove.assert_called_once()
    push_spy.assert_called_once_with("watchlist")
    assert app._priming_worker is None


def test_finish_loading_logs_when_indicator_missing(
    app: DoubloonApp,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Missing loading indicators should log but still push the screen."""

    def raise_no_matches(*_: Any, **__: Any) -> None:
        raise NoMatches("missing")

    monkeypatch.setattr(app, "query_one", raise_no_matches)
    push_spy = MagicMock()
    monkeypatch.setattr(app, "push_screen", push_spy)
    app._priming_worker = dummy_worker(is_running=False)

    with caplog.at_level(logging.ERROR):
        app._finish_loading()

    assert "No loading indicator found" in caplog.text
    push_spy.assert_called_once_with("watchlist")
    assert app._priming_worker is None
