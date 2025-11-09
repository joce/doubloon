"""Messages for DoubloonApp."""

from textual.message import Message

from calahan.yquote import YQuote

from .enums import SortDirection


# App messages
class AppExit(Message):
    """Message to request the app to exit."""


# Widget messages
class TableSortingChanged(Message):
    """Message to indicate that the table sorting has changed."""

    def __init__(self, column_key: str, direction: SortDirection) -> None:
        """Initialize the TableSortingChanged message.

        Args:
            column_key (key): The key of the column that is now sorted.
            direction (SortDirection): The direction of the sort.
        """

        super().__init__()
        self.column_key: str = column_key
        self.direction: SortDirection = direction


class QuotesRefreshed(Message):
    """Message to indicate that the quotes have been refreshed."""

    def __init__(self, quotes: list[YQuote]) -> None:
        """Initialize the QuotesRefreshed message.

        Args:
            quotes (list[YQuote]): The refreshed quotes.
        """

        super().__init__()
        self.quotes: list[YQuote] = quotes
