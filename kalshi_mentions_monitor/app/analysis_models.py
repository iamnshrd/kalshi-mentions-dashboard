from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(slots=True)
class StrikeRankItem:
    market_id: str
    label: str
    display_label: str
    score: int
    priority_band: str
    edge_tag: str
    strike_type: str
    yes_reference_price: float | None
    price_bucket: str
    reasons: list[str] = field(default_factory=list)
    status_class: str = 'status-gray'
    type_class: str = 'type-gray'

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StrikeAnalysis:
    market_id: str
    label: str
    short_label: str
    note: str
    bucket: str
    rank: StrikeRankItem

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EventAnalysis:
    group_key: str
    event_title: str
    event_ticker: str
    series_ticker: str
    status: str
    open_time: str
    close_time: str
    market_count: int
    dominant_group: str
    dominant_subtype: str
    dominant_rules_risk: str
    speaker: str
    format_confidence: float
    prep_focus: str
    live_focus: str
    priority: str
    strike_codes: list[str]
    strike_buckets: dict[str, Any]
    strike_intel: dict[str, list[dict[str, Any]]]
    strike_analyses: list[dict[str, Any]]
    context_checks: list[str]
    likely_hooks: list[str]
    context_notes: list[str]
    opening_plan: list[str]
    post_opening_plan: list[str]
    qa_transition_plan: list[str]
    strike_priority: dict[str, list[dict[str, Any]]]
    pre_event_summary: list[str]
    live_trading_summary: list[str]
    risk_summary: list[str]
    manual_trader_prompts: list[str]
    relevant_history_notes: list[str]
    consensus_misread: list[str]
    semantic_families: list[dict[str, Any]]
    attention_allocation: dict[str, Any]
    transcript_matches: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
