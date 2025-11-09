"""A simple footer with a clock."""

import sys

from textual.app import ComposeResult
from textual.widgets import Footer as TextualFooter

from .clock import Clock
from .enums import TimeFormat

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class Footer(TextualFooter):
    """The footer for the Doubloon app."""

    def __init__(self, time_format: TimeFormat) -> None:
        """Initialize the footer.

        This initializes the footer with a clock.
        """

        super().__init__()
        self._clock: Clock = Clock(time_format)

    @override
    def compose(self) -> ComposeResult:
        yield from super().compose()
        yield self._clock
