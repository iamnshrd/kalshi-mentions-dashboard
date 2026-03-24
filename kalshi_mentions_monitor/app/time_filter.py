from __future__ import annotations

import re
from datetime import UTC, date, datetime

from .models import NormalizedMarket

MONTHS = {
    'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
    'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12,
}


def _parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith('Z'):
            value = value[:-1] + '+00:00'
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _extract_date_from_text(value: str) -> date | None:
    if not value:
        return None
    m = re.search(r'(\d{2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(\d{2})', value.upper())
    if not m:
        return None
    day = int(m.group(1))
    month = MONTHS[m.group(2)]
    year = 2000 + int(m.group(3))
    try:
        return date(year, month, day)
    except Exception:
        return None


def market_reference_date(market: NormalizedMarket) -> date | None:
    # strongest signals first
    for raw in (market.close_time, market.open_time, market.created_time):
        dt = _parse_dt(raw)
        if dt:
            return dt.date()
    for raw in (market.event_ticker, market.ticker, market.title):
        d = _extract_date_from_text(raw)
        if d:
            return d
    return None


def is_relevant_from_date(market: NormalizedMarket, from_date: date) -> bool:
    ref = market_reference_date(market)
    if ref is None:
        return False
    return ref >= from_date


def today_utc() -> date:
    return datetime.now(UTC).date()
