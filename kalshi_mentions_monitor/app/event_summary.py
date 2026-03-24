from __future__ import annotations

import json
import re
from pathlib import Path
from collections import Counter

from .grouping import EventGroup
from .models import Classification, Recommendation
from .strike_intel import build_strike_intel, strike_label


def build_event_summary(group: EventGroup, classifications: dict[str, Classification], recommendations: dict[str, Recommendation]) -> dict:
    class_counter: Counter[str] = Counter()
    subtype_counter: Counter[str] = Counter()
    rules_counter: Counter[str] = Counter()

    for market in group.markets:
        c = classifications.get(market.market_id)
        if not c:
            continue
        class_counter[c.market_group] += 1
        subtype_counter[c.market_subtype] += 1
        rules_counter[c.rules_risk] += 1

    dominant_group = class_counter.most_common(1)[0][0] if class_counter else 'unclear_or_special'
    dominant_subtype = subtype_counter.most_common(1)[0][0] if subtype_counter else 'unknown'
    dominant_rules_risk = rules_counter.most_common(1)[0][0] if rules_counter else 'medium'

    speakers = [classifications[m.market_id].speaker for m in group.markets if m.market_id in classifications and classifications[m.market_id].speaker != 'unknown']
    speaker = speakers[0] if speakers else 'unknown'
    format_confidence = max([classifications[m.market_id].format_confidence for m in group.markets if m.market_id in classifications] or [0.5])

    pre: list[str] = []
    live: list[str] = []
    risk: list[str] = []
    for market in group.markets[:5]:
        rec = recommendations.get(market.market_id)
        if not rec:
            continue
        pre.extend(rec.pre_event_recommendations[:2])
        live.extend(rec.live_trading_recommendations[:2])
        risk.extend(rec.risk_notes[:2])

    def dedupe(xs: list[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for x in xs:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    if dominant_group == 'sports_announcer_mentions':
        prep_focus = 'Build announcer/network/game-state priors before market open.'
        live_focus = 'Reprice by game state, replay context, and commentary flow.'
        priority = 'high'
    elif dominant_group == 'earnings_or_corporate_mentions':
        prep_focus = 'Separate prepared-remarks phrases from analyst Q&A phrases.'
        live_focus = 'After prepared remarks, reprice all Q&A-heavy strikes immediately.'
        priority = 'normal'
    elif dominant_group == 'legal_court_mentions':
        prep_focus = 'Confirm who must say the phrase and what counts under the rules.'
        live_focus = 'Track speaker identity and oral-argument flow, not just isolated words.'
        priority = 'high'
    else:
        prep_focus = 'Check current events, event format, and strike clustering before trading.'
        live_focus = 'Use opening to identify the dominant theme cluster and repricing regime.'
        priority = 'high' if dominant_group == 'political_mentions' else 'normal'

    if dominant_rules_risk == 'high':
        priority = 'normal'

    strike_codes = [strike_label(m.market_id) for m in group.markets]
    strike_buckets = {
        'count': len(strike_codes),
        'context_sensitive_hint': len([x for x in strike_codes if x]),
    }

    first_classification = classifications.get(group.markets[0].market_id)
    strike_intel = build_strike_intel(group.markets, first_classification) if first_classification else {}

    return {
        'group_key': group.group_key,
        'event_title': group.event_title,
        'event_ticker': group.event_ticker,
        'series_ticker': group.series_ticker,
        'status': group.status,
        'open_time': group.open_time,
        'close_time': group.close_time,
        'market_count': len(group.markets),
        'dominant_group': dominant_group,
        'dominant_subtype': dominant_subtype,
        'dominant_rules_risk': dominant_rules_risk,
        'speaker': speaker,
        'format_confidence': round(format_confidence, 2),
        'prep_focus': prep_focus,
        'live_focus': live_focus,
        'priority': priority,
        'strike_codes': strike_codes,
        'strike_buckets': strike_buckets,
        'strike_intel': strike_intel,
        'pre_event_summary': dedupe(pre)[:8],
        'live_trading_summary': dedupe(live)[:8],
        'risk_summary': dedupe(risk)[:8],
    }


def write_event_summary(output_dir: Path, summary: dict) -> tuple[Path, Path]:
    event_dir = output_dir / 'events'
    (event_dir / 'markdown').mkdir(parents=True, exist_ok=True)
    (event_dir / 'json').mkdir(parents=True, exist_ok=True)
    slug = re.sub(r'[^a-z0-9]+', '-', (summary['event_title'] or summary['group_key']).lower()).strip('-')[:100] or 'event'
    md_path = event_dir / 'markdown' / f'{slug}.md'
    json_path = event_dir / 'json' / f'{slug}.json'

    lines = [
        '# Mention Event Summary',
        '',
        '## Event',
        f"- Title: {summary['event_title']}",
        f"- Event ticker: {summary['event_ticker'] or '-'}",
        f"- Series ticker: {summary['series_ticker'] or '-'}",
        f"- Status: {summary['status'] or '-'}",
        f"- Open time: {summary['open_time'] or '-'}",
        f"- Close time: {summary['close_time'] or '-'}",
        f"- Strike count: {summary['market_count']}",
        '',
        '## Classification',
        f"- Dominant group: {summary['dominant_group']}",
        f"- Dominant subtype: {summary['dominant_subtype']}",
        f"- Dominant rules risk: {summary['dominant_rules_risk']}",
        f"- Speaker: {summary['speaker']}",
        f"- Format confidence: {summary['format_confidence']}",
        f"- Priority: {summary['priority']}",
        '',
        '## Trader prep focus',
        f"- {summary['prep_focus']}",
        '',
        '## Trader live focus',
        f"- {summary['live_focus']}",
        '',
        '## Pre-event prep',
    ]
    lines.extend([f'- {x}' for x in summary['pre_event_summary']])
    lines.extend(['', '## Live trading guidance'])
    lines.extend([f'- {x}' for x in summary['live_trading_summary']])
    lines.extend(['', '## Risk notes'])
    lines.extend([f'- {x}' for x in summary['risk_summary']])
    lines.extend(['', '## Strikes'])
    lines.extend([f'- {x}' for x in summary['strike_codes']])
    lines.extend([
        '',
        '## Strike bucket notes',
        f"- Total strikes: {summary['strike_buckets']['count']}",
        f"- Context-sensitive hint count: {summary['strike_buckets']['context_sensitive_hint']}",
        '',
        '## Strike-level notes',
    ])
    for bucket in ['structural', 'qa_sensitive', 'contextual', 'game_state_sensitive', 'likely_trap']:
        items = summary['strike_intel'].get(bucket, [])
        if not items:
            continue
        lines.append(f'### {bucket}')
        for item in items[:8]:
            lines.append(f"- {item['note']}")
        lines.append('')

    md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return md_path, json_path
