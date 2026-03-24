from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class NormalizedMarket:
    market_id: str
    event_ticker: str
    ticker: str
    title: str
    subtitle: str
    yes_sub_title: str
    no_sub_title: str
    rules_primary: str
    rules_secondary: str
    status: str
    market_type: str
    series_ticker: str
    open_time: str
    close_time: str
    created_time: str
    updated_time: str
    yes_bid: float | None = None
    yes_ask: float | None = None
    no_bid: float | None = None
    no_ask: float | None = None
    yes_price: float | None = None
    no_price: float | None = None
    last_price: float | None = None
    volume: float | None = None
    raw_json: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Classification:
    market_id: str
    market_group: str
    market_subtype: str
    recurring_type: str
    phase_profile: str
    context_sensitivity: str
    rules_risk: str
    classification_confidence: float
    speaker: str
    format_confidence: float
    reasoning: list[str]


@dataclass(slots=True)
class Recommendation:
    market_id: str
    pre_event_recommendations: list[str]
    live_trading_recommendations: list[str]
    risk_notes: list[str]
    priority_level: str
