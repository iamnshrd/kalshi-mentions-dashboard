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
    rules_primary: str
    rules_secondary: str
    status: str
    open_time: str
    close_time: str
    created_time: str
    updated_time: str
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
    reasoning: list[str]


@dataclass(slots=True)
class Recommendation:
    market_id: str
    pre_event_recommendations: list[str]
    live_trading_recommendations: list[str]
    risk_notes: list[str]
    priority_level: str
