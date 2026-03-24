from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import re

from .grouping import EventGroup
from .models import Classification, Recommendation


def _strike_label(market_id: str) -> str:
    part = market_id.rsplit('-', 1)[-1]
    return part


def build_event_summary(group: EventGroup, classifications: dict[str, Classification], recommendations: dict[str, Recommendation]) -> dict:
    class_counter = Counter()
    subtype_counter = Counter()
    rules_counter = Counter()

    for market in group.markets:
        c = classifications.get(market.market_id)
        if not c:
            continue
        class_counter[c.market_group] += 1
        subtype_counter[c.market_subtype] += 1
        rules_counter[c.rules_risk] += 1

    dominant_group = class_counter.most_common(1)[0][0] if class_counter else "unclear_or_special"
    dominant_subtype = subtype_counter.most_common(1)[0][0] if subtype_counter else "unknown"
    dominant_rules_risk = rules_counter.most_common(1)[0][0] if rules_counter else "medium"

    pre = []
    live = []
    risk = []
    for market in group.markets[:5]:
        r = recommendations.get(market.market_id)
        if not r:
            continue
        pre.extend(r.pre_event_recommendations[:2])
        live.extend(r.live_trading_recommendations[:2])
        risk.extend(r.risk_notes[:2])

    def dedupe(xs):
        out=[]
        seen=set()
        for x in xs:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    strike_codes = [_strike_label(m.market_id) for m in group.markets]
    strike_buckets = {
        'all': strike_codes,
        'count': len(strike_codes),
        'context_sensitive_hint': len([s for s in strike_codes if len(s) > 0 and not s.isdigit()]),
    }

    return {
        "group_key": group.group_key,
        "event_title": group.event_title,
        "event_ticker": group.event_ticker,
        "series_ticker": group.series_ticker,
        "status": group.status,
        "open_time": group.open_time,
        "close_time": group.close_time,
        "market_count": len(group.markets),
        "dominant_group": dominant_group,
        "dominant_subtype": dominant_subtype,
        "dominant_rules_risk": dominant_rules_risk,
        "strike_codes": strike_codes,
        "strike_buckets": strike_buckets,
        "pre_event_summary": dedupe(pre)[:8],
        "live_trading_summary": dedupe(live)[:8],
        "risk_summary": dedupe(risk)[:8],
    }


def write_event_summary(output_dir: Path, summary: dict) -> tuple[Path, Path]:
    event_dir = output_dir / 'events'
    (event_dir / 'markdown').mkdir(parents=True, exist_ok=True)
    (event_dir / 'json').mkdir(parents=True, exist_ok=True)
    slug = re.sub(r'[^a-z0-9]+', '-', (summary['event_title'] or summary['group_key']).lower()).strip('-')[:100] or 'event'
    md_path = event_dir / 'markdown' / f'{slug}.md'
    json_path = event_dir / 'json' / f'{slug}.json'

    lines = [
        f"# Mention Event Summary",
        "",
        f"## Event",
        f"- Title: {summary['event_title']}",
        f"- Event ticker: {summary['event_ticker'] or '-'}",
        f"- Series ticker: {summary['series_ticker'] or '-'}",
        f"- Status: {summary['status'] or '-'}",
        f"- Open time: {summary['open_time'] or '-'}",
        f"- Close time: {summary['close_time'] or '-'}",
        f"- Strike count: {summary['market_count']}",
        "",
        "## Classification",
        f"- Dominant group: {summary['dominant_group']}",
        f"- Dominant subtype: {summary['dominant_subtype']}",
        f"- Dominant rules risk: {summary['dominant_rules_risk']}",
        "",
        "## Pre-event prep",
    ]
    lines.extend([f"- {x}" for x in summary['pre_event_summary']])
    lines.extend(["", "## Live trading guidance"])
    lines.extend([f"- {x}" for x in summary['live_trading_summary']])
    lines.extend(["", "## Risk notes"])
    lines.extend([f"- {x}" for x in summary['risk_summary']])
    lines.extend(["", "## Strikes"])
    lines.extend([f"- {x}" for x in summary['strike_codes']])
    lines.extend([
        "",
        "## Strike bucket notes",
        f"- Total strikes: {summary['strike_buckets']['count']}",
        f"- Context-sensitive hint count: {summary['strike_buckets']['context_sensitive_hint']}",
    ])
    md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return md_path, json_path
