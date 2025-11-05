"""Validate the behavior of the `YSearch` class."""

# cspell:disable

from __future__ import annotations

import zoneinfo
from datetime import date, datetime

from calahan import YSearchResult
from calahan.enums import QuoteType
from tests.fake_yfinance import FakeYFinance


async def test_ysearch_parses_quotes_section() -> None:
    """Ensure the YSearch model extracts quotes and converts fields appropriately."""

    search: YSearchResult = await FakeYFinance().search("BTC")

    assert search.count == 15
    assert len(search.quotes) == 7

    first_quote = search.quotes[0]
    assert first_quote.symbol == "BTC=F"
    assert first_quote.quote_type == QuoteType.FUTURE
    assert first_quote.short_name == "Bitcoin Futures,Oct-2025"
    assert first_quote.score == 30007.0
    assert first_quote.is_yahoo_finance is True

    equity_quote = search.quotes[5]
    assert equity_quote.quote_type == QuoteType.EQUITY
    assert equity_quote.long_name == "BTC Digital Ltd."
    assert equity_quote.sector == "Technology"
    assert equity_quote.industry_disp == "Computer Hardware"
    assert equity_quote.prev_name == "Meten EdtechX Education Group Ltd."
    assert equity_quote.name_change_date == date(2025, 11, 1)


def test_ysearch_parses_news_and_nav_sections() -> None:
    """Ensure the YSearch model extracts news and nav sections when present."""

    payload = {
        "count": 5,
        "quotes": [],
        "news": [
            {
                "uuid": "16c97176-f742-36e7-87c9-b7df95b48c93",
                "title": "Trump on Venezuela's Maduro amid another deadly boat strike",
                "publisher": "CBS News Videos",
                "link": "https://finance.yahoo.com/m/16c97176-f742-36e7-87c9-b7df95b48c93/trump-on-venezuela%27s-maduro.html",
                "providerPublishTime": 1762193478,
                "type": "VIDEO",
                "thumbnail": {
                    "resolutions": [
                        {
                            "url": "https://s.yimg.com/uu/api/res/1.2/PdwPT6AgQ37KW2Z2mq3AwA--~B/aD0xMDgwO3c9MTkyMDthcHBpZD15dGFjaHlvbg--/https://media.zenfs.com/en/video.cbsnewsvideos.com/c5d2d3186339e852907cfc436740f0ee",
                            "width": 1920,
                            "height": 1080,
                            "tag": "original",
                        },
                        {
                            "url": "https://s.yimg.com/uu/api/res/1.2/YwZ98E1SIokt4It2Z.GIvg--~B/Zmk9ZmlsbDtoPTE0MDtweW9mZj0wO3c9MTQwO2FwcGlkPXl0YWNoeW9u/https://media.zenfs.com/en/video.cbsnewsvideos.com/c5d2d3186339e852907cfc436740f0ee",
                            "width": 140,
                            "height": 140,
                            "tag": "140x140",
                        },
                    ]
                },
            },
            {
                "uuid": "91806467-ee39-3798-b273-c9f3e6c88df2",
                "title": "Trump says Maduro's days are numbered as strikes near Venezuela continue",
                "publisher": "CBS News Videos",
                "link": "https://finance.yahoo.com/m/91806467-ee39-3798-b273-c9f3e6c88df2/trump-says-maduro%27s-days-are.html",
                "providerPublishTime": 1762186280,
                "type": "VIDEO",
                "thumbnail": {
                    "resolutions": [
                        {
                            "url": "https://s.yimg.com/uu/api/res/1.2/ICQ.bmz_arCMpSgABqQD5Q--~B/aD0xMDgwO3c9MTkyMDthcHBpZD15dGFjaHlvbg--/https://media.zenfs.com/en/video.cbsnewsvideos.com/5fbfcd135a13a00124381ebf61d3d877",
                            "width": 1920,
                            "height": 1080,
                            "tag": "original",
                        },
                        {
                            "url": "https://s.yimg.com/uu/api/res/1.2/4oADdVXAjbpg5YUoib7fPQ--~B/Zmk9ZmlsbDtoPTE0MDtweW9mZj0wO3c9MTQwO2FwcGlkPXl0YWNoeW9u/https://media.zenfs.com/en/video.cbsnewsvideos.com/5fbfcd135a13a00124381ebf61d3d877",
                            "width": 140,
                            "height": 140,
                            "tag": "140x140",
                        },
                    ]
                },
            },
            {
                "uuid": "8ffd722b-1d20-31d6-8898-46a66863e628",
                "title": "Trump Claims He 'Doesn't Know' Who CZ Is Despite Presidential Pardon",
                "publisher": "CoinDesk",
                "link": "https://finance.yahoo.com/m/8ffd722b-1d20-31d6-8898-46a66863e628/trump-claims-he-%27doesn%27t.html",
                "providerPublishTime": 1762186878,
                "type": "VIDEO",
                "thumbnail": {
                    "resolutions": [
                        {
                            "url": "https://s.yimg.com/uu/api/res/1.2/__h2PN8ZdY3ns4_n7rJ.og--~B/aD00MDY7dz03MjA7YXBwaWQ9eXRhY2h5b24-/https://media.zenfs.com/en/coindesk_75/ac2ab7c18c4828af17866f2554004a10",
                            "width": 720,
                            "height": 406,
                            "tag": "original",
                        },
                        {
                            "url": "https://s.yimg.com/uu/api/res/1.2/fKC9lXJvB5Hxkb_8ZSHfyA--~B/Zmk9ZmlsbDtoPTE0MDtweW9mZj0wO3c9MTQwO2FwcGlkPXl0YWNoeW9u/https://media.zenfs.com/en/coindesk_75/ac2ab7c18c4828af17866f2554004a10",
                            "width": 140,
                            "height": 140,
                            "tag": "140x140",
                        },
                    ]
                },
                "relatedTickers": ["BTC-USD", "ETH-USD"],
            },
        ],
        "nav": [
            {
                "navName": "Trumponomics",
                "navUrl": "https://finance.yahoo.com/trumponomics",
            }
        ],
    }

    result = YSearchResult.model_validate(payload)

    assert len(result.news) == 3
    lead_story = result.news[0]
    assert lead_story.uuid == "16c97176-f742-36e7-87c9-b7df95b48c93"
    assert lead_story.provider_publish_time == datetime.fromtimestamp(
        1762193478, tz=zoneinfo.ZoneInfo("America/New_York")
    )
    assert lead_story.thumbnail is not None
    assert lead_story.thumbnail.resolutions[0].width == 1920

    coindesk_story = result.news[2]
    assert coindesk_story.related_tickers == ["BTC-USD", "ETH-USD"]

    assert len(result.nav) == 1
    nav_link = result.nav[0]
    assert nav_link.name == "Trumponomics"
    assert nav_link.url == "https://finance.yahoo.com/trumponomics"


def test_ysearch_parses_lists_section() -> None:
    """Ensure the YSearch model extracts search lists with optional attributes."""

    payload = {
        "count": 9,
        "quotes": [],
        "news": [],
        "nav": [],
        "lists": [
            {
                "slug": "most-active-penny-stocks",
                "name": "Most Active Penny Stocks",
                "index": "most-active-penny-stocks",
                "score": 40.163948,
                "type": "ALGO_WATCHLIST",
                "brandSlug": "yahoo-finance",
                "pfId": "most_active_penny_stocks",
                "symbolCount": 30,
                "dailyPercentGain": 48.94833790508765,
                "followerCount": 63066,
                "iconUrl": "https://edgecast-img.yahoo.net/mysterio/api/26a4087f26113a9f01fdb35c900a7112eaa81d24d74f9ca80fd3615e7f26a360/finance/resizefill_w96_h96/https://s.yimg.com/cv/apiv2/fin/img/assets/watchlist/penny-stocks-top-gainers.jpg",
                "userId": "X3NJ2A7VDSABUI4URBWME2PZNM",
            },
            {
                "index": "05f97149-f902-4cd3-8f72-f7768ac673e0",
                "id": "05f97149-f902-4cd3-8f72-f7768ac673e0",
                "title": "Most Actives - France",
                "canonicalName": "MOST_ACTIVES_FR",
                "score": 1.0,
                "type": "PREDEFINED_SCREENER",
                "total": 8512,
                "isPremium": False,
                "iconUrl": "https://edgecast-img.yahoo.net/mysterio/api/f041b4d17c09d0aa6923ce2533c3d27f341dd1600e3f8325b72e09010c455a87/finance/resizefill_w96_h96/https://s.yimg.com/cv/apiv2/fin/img/assets/predefined_screeners/analytics.png",
            },
        ],
    }

    result = YSearchResult.model_validate(payload)

    assert len(result.lists) == 2

    watchlist = result.lists[0]
    assert watchlist.list_type == "ALGO_WATCHLIST"
    assert watchlist.slug == "most-active-penny-stocks"
    assert watchlist.brand_slug == "yahoo-finance"
    assert watchlist.symbol_count == 30
    assert watchlist.daily_percent_gain == 48.94833790508765
    assert watchlist.follower_count == 63066
    assert watchlist.user_id == "X3NJ2A7VDSABUI4URBWME2PZNM"

    screener = result.lists[1]
    assert screener.list_type == "PREDEFINED_SCREENER"
    assert screener.id == "05f97149-f902-4cd3-8f72-f7768ac673e0"
    assert screener.title == "Most Actives - France"
    assert screener.canonical_name == "MOST_ACTIVES_FR"
    assert screener.total == 8512
    assert screener.is_premium is False
