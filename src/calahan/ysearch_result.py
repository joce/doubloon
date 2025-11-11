"""Provide structured access to Yahoo! Finance search results."""

# pyright: reportUnknownVariableType=none

from __future__ import annotations

from datetime import date, datetime  # noqa: TC003

from pydantic import AliasChoices, BaseModel, Field
from pydantic.alias_generators import to_camel

from .enums import QuoteType  # noqa: TC001


class YSearchQuote(BaseModel):
    """Structured representation of a single search result quote from Yahoo! Finance."""

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "alias_generator": to_camel,
    }

    exchange: str
    """Securities exchange on which the security is traded."""

    exchange_transfer_date: date | None = None
    """Date on which the security was transferred to a different exchange."""

    exch_disp: str
    """User-friendly representation of the exchange."""

    index: str
    """Index to which the security belongs."""

    industry: str | None = None
    """Industry of the company."""

    industry_disp: str | None = None
    """User-friendly representation of the industry."""

    is_yahoo_finance: bool
    """Indicates if the quote is from Yahoo! Finance."""

    long_name: str | None = Field(
        default=None, validation_alias=AliasChoices("longname")
    )
    """Official name of the company."""

    name_change_date: date | None = None
    """Date on which the company last changed its name."""

    new_listings_date: date | None = None
    """Date on which the company was newly listed."""

    prev_exchange: str | None = None
    """Exchange on which the security was previously traded."""

    prev_name: str | None = None
    """Name of the company prior to its most recent name change."""

    prev_ticker: str | None = None
    """Ticker symbol of the company prior to its most recent change."""

    quote_type: QuoteType
    """Type of quote."""

    score: float
    """Relevance score of the search result."""

    sector: str | None = None
    """Sector of the company."""

    short_name: str | None = Field(
        default=None, validation_alias=AliasChoices("shortname")
    )
    """Short, user-friendly name for the stock or security."""

    symbol: str
    """Ticker symbol of the security."""

    ticker_change_date: date | None = None
    """Date on which the ticker symbol was last changed."""

    type_disp: str
    """User-friendly representation of the QuoteType."""


class YSearchNewsThumbnailResolution(BaseModel):
    """Image resolution details for a search news item thumbnail."""

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "alias_generator": to_camel,
    }

    url: str
    """URL pointing to the image asset."""

    width: int
    """Image width in pixels."""

    height: int
    """Image height in pixels."""

    tag: str | None = None
    """Identifier describing the resolution variant."""


class YSearchNewsThumbnail(BaseModel):
    """Thumbnail information for a search news item."""

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "alias_generator": to_camel,
    }

    resolutions: list[YSearchNewsThumbnailResolution] = Field(default_factory=list)
    """Available thumbnail resolutions."""


class YSearchNews(BaseModel):
    """Structured representation of a news item returned by Yahoo! Finance search."""

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "alias_generator": to_camel,
    }

    uuid: str
    """Unique identifier for the news story."""

    title: str
    """Title of the news story."""

    publisher: str
    """Publisher providing the news story."""

    link: str
    """Link to the full news story."""

    provider_publish_time: datetime
    """Publication timestamp provided by Yahoo! Finance (in NY timezone)."""

    type: str
    """Type of content provided (e.g., STORY, VIDEO)."""

    thumbnail: YSearchNewsThumbnail | None = None
    """Thumbnail images associated with the story."""

    related_tickers: list[str] = Field(default_factory=list)
    """Tickers referenced in the story."""


class YSearchNavLink(BaseModel):
    """Navigation link returned with Yahoo! Finance search results."""

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "alias_generator": to_camel,
    }

    name: str = Field(validation_alias=AliasChoices("navName"))
    """Display name of the navigation link."""

    url: str = Field(validation_alias=AliasChoices("navUrl"))
    """Destination URL of the navigation link."""


class YSearchList(BaseModel):
    """List metadata returned with Yahoo! Finance search results."""

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "alias_generator": to_camel,
    }

    list_type: str = Field(validation_alias=AliasChoices("type"))
    """Classifier describing the list category (e.g., ALGO_WATCHLIST)."""

    index: str
    """Identifier describing the list within Yahoo! Finance."""

    score: float
    """Relevance score supplied by the search service."""

    icon_url: str | None = None
    """URL pointing to an icon representing the list."""

    slug: str | None = None
    """URL-friendly identifier for the list when available."""

    name: str | None = None
    """Human-readable name for the list."""

    brand_slug: str | None = None
    """Brand identifier associated with the list."""

    pf_id: str | None = None
    """Portfolio identifier used internally by Yahoo! Finance."""

    symbol_count: int | None = None
    """Number of symbols tracked by the list."""

    daily_percent_gain: float | None = None
    """Percentage gain for the list over the last trading day."""

    follower_count: int | None = None
    """Number of Yahoo! Finance users following the list."""

    user_id: str | None = None
    """Author identifier when the list is user generated."""

    id: str | None = None
    """Unique identifier used by screener-based lists."""

    title: str | None = None
    """Title describing the list."""

    canonical_name: str | None = None
    """Canonical identifier for the list."""

    total: int | None = None
    """Total number of results surfaced by the list."""

    is_premium: bool | None = None
    """Indicates whether the list requires a premium subscription."""


class YSearchResult(BaseModel):
    """Structured representation of Yahoo! Finance search results."""

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
        "alias_generator": to_camel,
        "extra": "ignore",
    }

    count: int = 0
    """Number of search results returned."""

    quotes: list[YSearchQuote] = Field(default_factory=list)
    """Quotes returned for the provided search query."""

    news: list[YSearchNews] = Field(default_factory=list)
    """News articles associated with the search query."""

    lists: list[YSearchList] = Field(default_factory=list)
    """Curated lists such as algorithmic watchlists and screeners."""

    nav: list[YSearchNavLink] = Field(default_factory=list)
    """Navigation links provided with the search results."""
