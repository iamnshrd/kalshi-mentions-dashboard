from __future__ import annotations

import re
from dataclasses import dataclass

from .models import NormalizedMarket

MENTION_HINTS = {
    "what will": 4,
    "say during": 5,
    "say in": 4,
    "mention": 4,
    "remarks": 3,
    "press conference": 4,
    "press briefing": 4,
    "speech": 2,
    "interview": 3,
    "earnings call": 4,
    "during the game": 5,
    "during the broadcast": 5,
    "during the show": 4,
    "during the ceremony": 4,
    "during the halftime show": 5,
    "what will .* say": 6,
}

SPORTS_BROADCAST_HINTS = {
    "announcer": 4,
    "commentator": 4,
    "broadcast": 3,
    "pregame": 2,
    "postgame": 2,
    "halftime": 2,
}

NEGATIVE_HINTS = {
    "wins by": -5,
    "points": -2,
    "rebounds": -2,
    "assists": -2,
    "temperature": -5,
    "rain": -5,
}


@dataclass(slots=True)
class MentionHeuristicResult:
    is_candidate: bool
    score: int
    reasons: list[str]
    text: str


def normalize_text(*parts: str) -> str:
    text = " ".join(p for p in parts if p).lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_market_text(market: NormalizedMarket) -> str:
    return normalize_text(
        market.title,
        market.subtitle,
        market.yes_sub_title,
        market.no_sub_title,
        market.rules_primary,
        market.rules_secondary,
        market.event_ticker,
        market.series_ticker,
        market.market_type,
    )


def score_market_for_mentions(market: NormalizedMarket) -> MentionHeuristicResult:
    text = build_market_text(market)
    score = 0
    reasons: list[str] = []

    for hint, weight in MENTION_HINTS.items():
        if hint.startswith("what will .*"):
            if re.search(hint, text):
                score += weight
                reasons.append(f"pattern:{hint}+{weight}")
        elif hint in text:
            score += weight
            reasons.append(f"hint:{hint}+{weight}")

    for hint, weight in SPORTS_BROADCAST_HINTS.items():
        if hint in text and any(x in text for x in ["say", "mention", "during the game", "during the broadcast"]):
            score += weight
            reasons.append(f"sports_hint:{hint}+{weight}")

    for hint, weight in NEGATIVE_HINTS.items():
        if hint in text and not any(x in text for x in ["say", "mention", "remarks", "interview", "speech", "during the game", "during the broadcast"]):
            score += weight
            reasons.append(f"negative:{hint}{weight}")

    if market.market_type == "binary":
        score += 1
        reasons.append("binary+1")

    if market.series_ticker and any(x in market.series_ticker.lower() for x in ["speak", "mention", "broadcast", "remarks"]):
        score += 4
        reasons.append("series_ticker_hint+4")

    is_candidate = score >= 5
    return MentionHeuristicResult(is_candidate=is_candidate, score=score, reasons=reasons, text=text)


def looks_like_mention_market(market: NormalizedMarket) -> bool:
    return score_market_for_mentions(market).is_candidate
