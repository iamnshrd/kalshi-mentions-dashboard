from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def build_health_summary(db_path: Path) -> dict:
    if not db_path.exists():
        return {'status': 'no_db'}
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        last_run = conn.execute('SELECT * FROM poll_runs ORDER BY run_id DESC LIMIT 1').fetchone()
        market_error_count = conn.execute('SELECT COUNT(*) AS c FROM market_errors').fetchone()['c']
        recent_errors = conn.execute('SELECT market_id, stage, error, created_at FROM market_errors ORDER BY id DESC LIMIT 10').fetchall()
        market_count = conn.execute('SELECT COUNT(*) AS c FROM markets').fetchone()['c']
        classification_count = conn.execute('SELECT COUNT(*) AS c FROM classifications').fetchone()['c']
        recommendation_count = conn.execute('SELECT COUNT(*) AS c FROM recommendations').fetchone()['c']
        return {
            'status': 'ok',
            'markets': market_count,
            'classifications': classification_count,
            'recommendations': recommendation_count,
            'market_errors': market_error_count,
            'last_run': dict(last_run) if last_run else None,
            'recent_errors': [dict(r) for r in recent_errors],
        }
    finally:
        conn.close()


def health_to_text(summary: dict) -> str:
    return json.dumps(summary, ensure_ascii=False, indent=2)
