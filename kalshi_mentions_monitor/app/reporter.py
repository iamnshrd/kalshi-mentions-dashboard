from __future__ import annotations

import json
import re
from pathlib import Path

from .models import Classification, NormalizedMarket, Recommendation


def _slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:80] or "market"


def write_reports(output_dir: Path, market: NormalizedMarket, c: Classification, r: Recommendation) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    md_dir = output_dir / "markdown"
    json_dir = output_dir / "json"
    md_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)

    slug = _slugify(market.title or market.market_id)
    md_path = md_dir / f"{slug}.md"
    json_path = json_dir / f"{slug}.json"

    markdown = _build_markdown(market, c, r)
    md_path.write_text(markdown, encoding="utf-8")

    payload = {
        "market": market.raw_json,
        "normalized": {
            "market_id": market.market_id,
            "event_ticker": market.event_ticker,
            "title": market.title,
            "subtitle": market.subtitle,
            "yes_sub_title": market.yes_sub_title,
            "no_sub_title": market.no_sub_title,
            "series_ticker": market.series_ticker,
            "market_type": market.market_type,
            "status": market.status,
            "open_time": market.open_time,
            "close_time": market.close_time,
        },
        "classification": {
            "market_group": c.market_group,
            "market_subtype": c.market_subtype,
            "recurring_type": c.recurring_type,
            "phase_profile": c.phase_profile,
            "context_sensitivity": c.context_sensitivity,
            "rules_risk": c.rules_risk,
            "classification_confidence": c.classification_confidence,
            "reasoning": c.reasoning,
        },
        "recommendation": {
            "pre_event_recommendations": r.pre_event_recommendations,
            "live_trading_recommendations": r.live_trading_recommendations,
            "risk_notes": r.risk_notes,
            "priority_level": r.priority_level,
        },
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return md_path, json_path


def _build_markdown(market: NormalizedMarket, c: Classification, r: Recommendation) -> str:
    lines = [
        "# New Mention Market Detected",
        "",
        "## Market",
        f"- Title: {market.title}",
        f"- Subtitle: {market.subtitle or '-'}",
        f"- Ticker: {market.market_id}",
        f"- Event ticker: {market.event_ticker or '-'}",
        f"- Status: {market.status or '-'}",
        f"- Open time: {market.open_time or '-'}",
        f"- Close time: {market.close_time or '-'}",
        "",
        "## Classification",
        f"- Group: {c.market_group}",
        f"- Subtype: {c.market_subtype}",
        f"- Recurring: {c.recurring_type}",
        f"- Phase profile: {c.phase_profile}",
        f"- Context sensitivity: {c.context_sensitivity}",
        f"- Rules risk: {c.rules_risk}",
        f"- Confidence: {c.classification_confidence}",
        "",
        "## Reasoning",
    ]
    lines.extend([f"- {x}" for x in c.reasoning] or ["- No reasoning available"])
    lines.extend([
        "",
        "## Pre-event prep",
    ])
    lines.extend([f"- {x}" for x in r.pre_event_recommendations])
    lines.extend([
        "",
        "## Live trading guidance",
    ])
    lines.extend([f"- {x}" for x in r.live_trading_recommendations])
    lines.extend([
        "",
        "## Risk notes",
    ])
    lines.extend([f"- {x}" for x in r.risk_notes])
    return "\n".join(lines) + "\n"
