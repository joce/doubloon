"""The doubloon application."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from textual import work
from textual.app import App, ComposeResult
from textual.css.query import NoMatches
from textual.logging import TextualHandler
from textual.widgets import LoadingIndicator

from calahan import YFinance

from .doubloon_config import DoubloonConfig
from .footer import Footer
from .watchlist_screen import WatchlistScreen

if TYPE_CHECKING:
    from io import TextIOWrapper

    from rich.console import RenderableType
    from textual.worker import Worker

    from .messages import AppExit

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

logging.basicConfig(
    level=logging.NOTSET,
    handlers=[TextualHandler()],
)
logging.getLogger("asyncio").setLevel(logging.ERROR)

_LOGGER = logging.getLogger(__name__)


class DoubloonApp(App[None]):
    """A Textual app for the Doubloon application."""

    CSS_PATH = "./doubloonapp.tcss"

    ENABLE_COMMAND_PALETTE = False  # TODO: Consider enabling this

    def __init__(self) -> None:
        """Initialize the main application components and state management."""

        super().__init__()

        self._yfinance = YFinance()
        self._config = DoubloonConfig()
        self._priming_worker: Worker[None] | None = None

        self._config_loaded = False

        self._may_exit = False

        # Widgets
        self._footer = Footer(self._config.time_format)

    @property
    def config(self) -> DoubloonConfig:
        """Get the current configuration.

        Returns:
            The current configuration.
        """

        return self._config

    @property
    def yfinance(self) -> YFinance:
        """Get the YFinance client.

        Returns:
            The YFinance client.
        """

        return self._yfinance

    @override
    def compose(self) -> ComposeResult:
        yield LoadingIndicator()
        yield self._footer

    def on_unmount(self) -> None:
        """Handle unmount events."""

        if self._priming_worker is not None and self._priming_worker.is_running:
            self._priming_worker.cancel()

    def on_mount(self) -> None:
        """Handle mount events."""

        self._priming_worker = self._prime_yfinance()
        self.title = self._config.title
        self.install_screen(  # type: ignore[no-untyped-call]
            WatchlistScreen(), name="watchlist"
        )

    async def on_app_exit(self, _: AppExit) -> None:
        """Handle exit app messages.

        Do not call this directly.
        """

        if self._priming_worker and self._priming_worker.is_running:
            self._priming_worker.cancel()
        try:
            await self._yfinance.aclose()
        except Exception:
            logging.getLogger(__name__).exception("Error closing YFinance")

        self._may_exit = True
        self.exit()

    @override
    def exit(
        self,
        result: None = None,
        return_code: int = 0,
        message: RenderableType | None = None,
    ) -> None:
        """Guarded exit: only proceeds if async cleanup enabled it.

        Do not call this directly. Post a ExitApp message to initiate quitting.

        Args:
            result: The result to return (None).
            return_code: The return code (0).
            message: An optional message to display on exit.

        Raises:
            RuntimeError: If called directly without async cleanup.
        """

        if not self._may_exit:
            msg = "Blocked direct exit(); use ExitApp message instead."
            raise RuntimeError(msg)

        self._may_exit = False
        super().exit(result, return_code, message)

    def load_config(self, path: str) -> None:
        """Load the configuration for the app.

        Args:
            path: The path to the configuration file.
        """

        if self._config_loaded:
            return

        try:
            f: TextIOWrapper
            with Path(path).open(encoding="utf-8") as f:
                if Path(path).stat().st_size == 0:
                    _LOGGER.warning("load_config: Config file is empty: %s", path)
                else:
                    config_data: dict[str, Any] = json.load(f)
                    # Use Pydantic's model_validate to create a new config instance
                    self._config = DoubloonConfig.model_validate(config_data)
                    self._config_loaded = True
        except FileNotFoundError:
            _LOGGER.warning("load_config: Config file not found: %s", path)
        except json.JSONDecodeError as e:
            _LOGGER.exception(
                "load_config: error decoding JSON file: %s [%d, %d]: %s",
                path,
                e.lineno,
                e.colno,
                e.msg,
            )

        if not self._config_loaded:
            _LOGGER.info("Using default configuration")
            self._config = DoubloonConfig()
            self._config_loaded = True

        # TODO: asyncio's logging needs to be set as the same level as the app's

    def save_config(self, path: str) -> None:
        """Save the configuration for the app.

        Args:
            path: The path to the configuration file.
        """

        try:
            f: TextIOWrapper
            with Path(path).open("w+", encoding="utf-8") as f:
                # Use Pydantic's model_dump to serialize the config
                config_data: dict[str, Any] = self._config.model_dump(mode="json")
                json.dump(config_data, f, indent=4)
        except FileNotFoundError:
            _LOGGER.exception("save_config: Config file not found: %s", path)
        except PermissionError:
            _LOGGER.exception("save_config: Permission denied: %s", path)

    @work(exclusive=True)
    async def _prime_yfinance(self) -> None:
        """Prime the YFinance client."""

        await self._yfinance.prime()
        if self._priming_worker is not None and not self._priming_worker.is_cancelled:
            self._finish_loading()

    def _finish_loading(self) -> None:
        """Finish loading."""

        try:
            indicator: LoadingIndicator = self.query_one(
                "LoadingIndicator", LoadingIndicator
            )
            indicator.remove()
        except NoMatches:
            # No indicator was found
            _LOGGER.exception("No loading indicator found")

        self.push_screen("watchlist")

        self._priming_worker = None
