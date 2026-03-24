from __future__ import annotations

import json
import re
from pathlib import Path

from .analysis_models import EventAnalysis


def write_event_summary(output_dir: Path, summary: EventAnalysis | dict) -> tuple[Path, Path]:
    data = summary.to_dict() if hasattr(summary, 'to_dict') else summary
    event_dir = output_dir / 'events'
    (event_dir / 'markdown').mkdir(parents=True, exist_ok=True)
    (event_dir / 'json').mkdir(parents=True, exist_ok=True)
    slug = re.sub(r'[^a-z0-9]+', '-', (data['event_title'] or data['group_key']).lower()).strip('-')[:100] or 'event'
    md_path = event_dir / 'markdown' / f'{slug}.md'
    json_path = event_dir / 'json' / f'{slug}.json'

    lines = [
        '# Mention Event Summary', '', '## Event',
        f"- Title: {data['event_title']}",
        f"- Event ticker: {data['event_ticker'] or '-'}",
        f"- Series ticker: {data['series_ticker'] or '-'}",
        f"- Status: {data['status'] or '-'}",
        f"- Open time: {data['open_time'] or '-'}",
        f"- Close time: {data['close_time'] or '-'}",
        f"- Strike count: {data['market_count']}", '', '## Classification',
        f"- Dominant group: {data['dominant_group']}",
        f"- Dominant subtype: {data['dominant_subtype']}",
        f"- Dominant rules risk: {data['dominant_rules_risk']}",
        f"- Speaker: {data['speaker']}",
        f"- Format confidence: {data['format_confidence']}",
        f"- Priority: {data['priority']}", '', '## Trader prep focus',
        f"- {data['prep_focus']}", '', '## Trader live focus', f"- {data['live_focus']}", '', '## Strike ranking',
    ]
    for item in data['strike_priority']['top_watchlist']:
        price = item['yes_reference_price']
        price_text = '-' if price is None else f"{price:g}"
        display = item.get('display_label', item['label'])
        lines.append(f"- {display} [{item['priority_band']} | {item['edge_tag']} | yes≈{price_text}] — {'; '.join(item['reasons'])}")
    lines.extend(['', '## Context checks'])
    lines.extend([f'- {x}' for x in data['context_checks']])
    lines.extend(['', '## Pre-event prep'])
    lines.extend([f'- {x}' for x in data['pre_event_summary']])
    lines.extend(['', '## Opening plan'])
    lines.extend([f'- {x}' for x in data['opening_plan']])
    lines.extend(['', '## Live trading guidance'])
    lines.extend([f'- {x}' for x in data['live_trading_summary']])
    lines.extend(['', '## Risk notes'])
    lines.extend([f'- {x}' for x in data['risk_summary']])

    md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return md_path, json_path
