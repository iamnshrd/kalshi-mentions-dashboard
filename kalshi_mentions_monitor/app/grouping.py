from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from .models import NormalizedMarket


@dataclass(slots=True)
class EventGroup:
    group_key: str
    event_ticker: str
    series_ticker: str
    event_title: str
    status: str
    open_time: str
    close_time: str
    markets: list[NormalizedMarket] = field(default_factory=list)


def _extract_event_title(title: str) -> str:
    if not title:
        return "Unknown mention event"
    m = re.match(r"What will (.+?) say during (.+?)\?", title, flags=re.IGNORECASE)
    if m:
        speaker = m.group(1).strip()
        event = m.group(2).strip()
        return f"{speaker} — {event}"
    m2 = re.match(r"What will the announcers say during (.+?)\?", title, flags=re.IGNORECASE)
    if m2:
        return f"Announcers — {m2.group(1).strip()}"
    return title.strip()


def group_markets(markets: list[NormalizedMarket]) -> list[EventGroup]:
    grouped: dict[str, list[NormalizedMarket]] = defaultdict(list)
    for market in markets:
        key = market.event_ticker or market.series_ticker or market.market_id
        grouped[key].append(market)

    out: list[EventGroup] = []
    for key, items in grouped.items():
        items_sorted = sorted(items, key=lambda m: m.market_id)
        first = items_sorted[0]
        event_title = _extract_event_title(first.title)
        out.append(
            EventGroup(
                group_key=key,
                event_ticker=first.event_ticker,
                series_ticker=first.series_ticker,
                event_title=event_title,
                status=first.status,
                open_time=first.open_time,
                close_time=first.close_time,
                markets=items_sorted,
            )
        )
    return sorted(out, key=lambda g: (g.open_time or "", g.group_key))
