"""A very simple and limited widget to display the current time."""

from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime
from time import strftime

from textual.widgets import Static

from .enums import TimeFormat


class Clock(Static):
    """A very simple and limited widget to display the current time."""

    def __init__(self, time_format: TimeFormat) -> None:
        super().__init__()
        self._time_format: TimeFormat = time_format
        self._clock_task: asyncio.Task[None] | None = None

    @property
    def time_format(self) -> TimeFormat:
        """The time format."""

        return self._time_format

    @time_format.setter
    def time_format(self, value: TimeFormat) -> None:
        if value == self._time_format:
            return
        self._time_format = value

    async def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""

        self._clock_task = asyncio.create_task(self._run_clock_loop())

    async def on_unmount(self) -> None:
        """Cancel the update task if the widget is unmounted."""
        if self._clock_task:
            self._clock_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._clock_task

    async def _run_clock_loop(self) -> None:
        """Loop that updates the clock in sync with system time."""
        while True:
            self._show_time()

            # Current wall time in fractional seconds
            now = datetime.now().astimezone()
            micros = now.microsecond / 1_000_000
            delay = 1.0 - micros

            await asyncio.sleep(delay)

    def _show_time(self) -> None:
        """Update the time displayed by the widget."""

        if self._time_format == TimeFormat.TWENTY_FOUR_HOUR:
            self.update(strftime("%H:%M:%S"))
        else:
            self.update(strftime("%I:%M:%S %p"))
