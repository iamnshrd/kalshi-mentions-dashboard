from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .models import Classification, NormalizedMarket, Recommendation


SCHEMA = """
CREATE TABLE IF NOT EXISTS markets (
    market_id TEXT PRIMARY KEY,
    event_ticker TEXT,
    ticker TEXT,
    title TEXT,
    subtitle TEXT,
    yes_sub_title TEXT,
    no_sub_title TEXT,
    rules_primary TEXT,
    rules_secondary TEXT,
    status TEXT,
    market_type TEXT,
    series_ticker TEXT,
    open_time TEXT,
    close_time TEXT,
    created_time TEXT,
    updated_time TEXT,
    raw_json TEXT,
    first_seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS classifications (
    market_id TEXT PRIMARY KEY,
    market_group TEXT,
    market_subtype TEXT,
    recurring_type TEXT,
    phase_profile TEXT,
    context_sensitivity TEXT,
    rules_risk TEXT,
    classification_confidence REAL,
    reasoning TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommendations (
    market_id TEXT PRIMARY KEY,
    pre_event_recommendations TEXT,
    live_trading_recommendations TEXT,
    risk_notes TEXT,
    priority_level TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS poll_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT,
    finished_at TEXT,
    markets_fetched INTEGER,
    mention_candidates INTEGER,
    new_markets_found INTEGER,
    errors TEXT
);
"""


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            conn.close()

    def market_exists(self, market_id: str) -> bool:
        with self.connect() as conn:
            row = conn.execute("SELECT 1 FROM markets WHERE market_id = ?", (market_id,)).fetchone()
            return row is not None

    def upsert_market(self, market: NormalizedMarket) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO markets (
                    market_id, event_ticker, ticker, title, subtitle, yes_sub_title, no_sub_title, rules_primary,
                    rules_secondary, status, market_type, series_ticker, open_time, close_time, created_time,
                    updated_time, raw_json, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(market_id) DO UPDATE SET
                    event_ticker=excluded.event_ticker,
                    ticker=excluded.ticker,
                    title=excluded.title,
                    subtitle=excluded.subtitle,
                    yes_sub_title=excluded.yes_sub_title,
                    no_sub_title=excluded.no_sub_title,
                    rules_primary=excluded.rules_primary,
                    rules_secondary=excluded.rules_secondary,
                    status=excluded.status,
                    market_type=excluded.market_type,
                    series_ticker=excluded.series_ticker,
                    open_time=excluded.open_time,
                    close_time=excluded.close_time,
                    created_time=excluded.created_time,
                    updated_time=excluded.updated_time,
                    raw_json=excluded.raw_json,
                    last_seen_at=CURRENT_TIMESTAMP
                """,
                (
                    market.market_id,
                    market.event_ticker,
                    market.ticker,
                    market.title,
                    market.subtitle,
                    market.yes_sub_title,
                    market.no_sub_title,
                    market.rules_primary,
                    market.rules_secondary,
                    market.status,
                    market.market_type,
                    market.series_ticker,
                    market.open_time,
                    market.close_time,
                    market.created_time,
                    market.updated_time,
                    json.dumps(market.raw_json),
                ),
            )
            conn.commit()

    def upsert_classification(self, c: Classification) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO classifications (
                    market_id, market_group, market_subtype, recurring_type,
                    phase_profile, context_sensitivity, rules_risk,
                    classification_confidence, reasoning, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
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
                """,
                (
                    c.market_id,
                    c.market_group,
                    c.market_subtype,
                    c.recurring_type,
                    c.phase_profile,
                    c.context_sensitivity,
                    c.rules_risk,
                    c.classification_confidence,
                    json.dumps(c.reasoning),
                ),
            )
            conn.commit()

    def upsert_recommendation(self, r: Recommendation) -> None:
        with self.connect() as conn:
            conn.execute(
                """
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
                """,
                (
                    r.market_id,
                    json.dumps(r.pre_event_recommendations),
                    json.dumps(r.live_trading_recommendations),
                    json.dumps(r.risk_notes),
                    r.priority_level,
                ),
            )
            conn.commit()

    def log_poll_run(self, started_at: str, finished_at: str, markets_fetched: int, mention_candidates: int, new_markets_found: int, errors: str = "") -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO poll_runs (started_at, finished_at, markets_fetched, mention_candidates, new_markets_found, errors) VALUES (?, ?, ?, ?, ?, ?)",
                (started_at, finished_at, markets_fetched, mention_candidates, new_markets_found, errors),
            )
            conn.commit()
