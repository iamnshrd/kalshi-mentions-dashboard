from __future__ import annotations

import re

from .models import NormalizedMarket

MENTION_HINTS = [
    "what will",
    "say during",
    "say in",
    "mention",
    "remarks",
    "press conference",
    "speech",
    "interview",
    "earnings call",
    "during the game",
    "during the broadcast",
    "during the show",
    "during the ceremony",
    "during the halftime show",
]

EXCLUDE_HINTS = [
    "wins by",
    "points",
    "rebounds",
    "assists",
    "temperature",
    "rain",
    "nba",
    "nhl",
]


def normalize_text(*parts: str) -> str:
    text = " ".join(p for p in parts if p).lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def looks_like_mention_market(market: NormalizedMarket) -> bool:
    text = normalize_text(market.title, market.subtitle, market.rules_primary, market.rules_secondary, market.event_ticker)
    if any(h in text for h in MENTION_HINTS):
        return True
    if any(h in text for h in EXCLUDE_HINTS) and not any(h in text for h in ["say", "mention", "remarks", "interview", "speech"]):
        return False
    patterns = [
        r"what will .* say",
        r"what will .* mention",
        r"during .* remarks",
        r"during .* press conference",
        r"during .* interview",
        r"during the game",
    ]
    return any(re.search(p, text) for p in patterns)
