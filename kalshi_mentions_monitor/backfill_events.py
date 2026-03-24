from __future__ import annotations

import json
import sqlite3
from pathlib import Path
import sys

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kalshi_mentions_monitor.app.config import Settings
from kalshi_mentions_monitor.app.classifier import classify_market
from kalshi_mentions_monitor.app.event_summary import build_event_summary
from kalshi_mentions_monitor.app.event_writer import write_event_summary
from kalshi_mentions_monitor.app.grouping import group_markets
from kalshi_mentions_monitor.app.models import Classification, NormalizedMarket, Recommendation
from kalshi_mentions_monitor.app.dashboard import render_dashboard
from kalshi_mentions_monitor.app.deploy import maybe_deploy_dashboard
from kalshi_mentions_monitor.app.recommender import build_recommendation


def _loads(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def main() -> None:
    s = Settings()
    conn = sqlite3.connect(s.db_path)
    conn.row_factory = sqlite3.Row
    try:
        market_rows = conn.execute('SELECT * FROM markets ORDER BY event_ticker, market_id').fetchall()
        markets: list[NormalizedMarket] = []
        for row in market_rows:
            raw = _loads(row['raw_json'], {})
            markets.append(NormalizedMarket(
                market_id=row['market_id'],
                event_ticker=row['event_ticker'] or '',
                ticker=row['ticker'] or '',
                title=row['title'] or '',
                subtitle=row['subtitle'] or '',
                yes_sub_title=row['yes_sub_title'] or '',
                no_sub_title=row['no_sub_title'] or '',
                rules_primary=row['rules_primary'] or '',
                rules_secondary=row['rules_secondary'] or '',
                status=row['status'] or '',
                market_type=row['market_type'] or '',
                series_ticker=row['series_ticker'] or '',
                open_time=row['open_time'] or '',
                close_time=row['close_time'] or '',
                created_time=row['created_time'] or '',
                updated_time=row['updated_time'] or '',
                yes_bid=raw.get('yes_bid_dollars') or raw.get('yes_bid'),
                yes_ask=raw.get('yes_ask_dollars') or raw.get('yes_ask'),
                no_bid=raw.get('no_bid_dollars') or raw.get('no_bid'),
                no_ask=raw.get('no_ask_dollars') or raw.get('no_ask'),
                yes_price=raw.get('last_price_dollars') or raw.get('yes_price'),
                no_price=raw.get('no_price_dollars') or raw.get('no_price'),
                last_price=raw.get('last_price_dollars') or raw.get('last_price'),
                volume=raw.get('volume_24h_fp') or raw.get('volume_fp') or raw.get('volume'),
                raw_json=raw,
            ))

        classifications = {}
        recommendations = {}
        for market in markets:
            c = classify_market(market)
            r = build_recommendation(market, c)
            classifications[market.market_id] = c
            recommendations[market.market_id] = r
            conn.execute(
                '''
                INSERT INTO classifications (
                    market_id, market_group, market_subtype, recurring_type,
                    phase_profile, context_sensitivity, rules_risk,
                    classification_confidence, speaker, format_confidence,
                    reasoning, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(market_id) DO UPDATE SET
                    market_group=excluded.market_group,
                    market_subtype=excluded.market_subtype,
                    recurring_type=excluded.recurring_type,
                    phase_profile=excluded.phase_profile,
                    context_sensitivity=excluded.context_sensitivity,
                    rules_risk=excluded.rules_risk,
                    classification_confidence=excluded.classification_confidence,
                    speaker=excluded.speaker,
                    format_confidence=excluded.format_confidence,
                    reasoning=excluded.reasoning,
                    updated_at=CURRENT_TIMESTAMP
                ''',
                (
                    c.market_id, c.market_group, c.market_subtype, c.recurring_type, c.phase_profile,
                    c.context_sensitivity, c.rules_risk, c.classification_confidence, c.speaker,
                    c.format_confidence, json.dumps(c.reasoning, ensure_ascii=False),
                ),
            )
            conn.execute(
                '''
                INSERT INTO recommendations (
                    market_id, pre_event_recommendations, live_trading_recommendations,
                    risk_notes, priority_level, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(market_id) DO UPDATE SET
                    pre_event_recommendations=excluded.pre_event_recommendations,
                    live_trading_recommendations=excluded.live_trading_recommendations,
                    risk_notes=excluded.risk_notes,
                    priority_level=excluded.priority_level,
                    updated_at=CURRENT_TIMESTAMP
                ''',
                (
                    r.market_id,
                    json.dumps(r.pre_event_recommendations, ensure_ascii=False),
                    json.dumps(r.live_trading_recommendations, ensure_ascii=False),
                    json.dumps(r.risk_notes, ensure_ascii=False),
                    r.priority_level,
                ),
            )
        conn.commit()

        count = 0
        for group in group_markets(markets):
            summary = build_event_summary(group, classifications, recommendations)
            write_event_summary(s.output_dir, summary)
            count += 1

        dashboard_path, dashboard_events = render_dashboard(s.output_dir)
        deploy = maybe_deploy_dashboard(Path(s.output_dir).parent)
        print(json.dumps({'events_rebuilt': count, 'dashboard_path': str(dashboard_path), 'dashboard_events': dashboard_events, 'deploy': deploy}, ensure_ascii=False, indent=2))
    finally:
        conn.close()


if __name__ == '__main__':
    main()
