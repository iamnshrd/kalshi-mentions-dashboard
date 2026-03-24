# Kalshi Mentions Monitor

MVP service that polls Kalshi every 5 minutes, detects new mention-like markets, classifies them, and generates pre-event + live trading recommendations.

## Features
- Polls Kalshi markets endpoint on a fixed cadence
- Detects new markets via SQLite persistence
- Applies rule-based mention filtering and market classification
- Generates pre-event, live-trading, and risk-note recommendations
- Writes markdown and JSON summaries for newly discovered markets
- Can run once or as a long-running daemon loop

## Layout
- `app/config.py` runtime settings
- `app/db.py` SQLite schema + persistence helpers
- `app/kalshi_client.py` API client
- `app/filtering.py` mention-market heuristics
- `app/classifier.py` market classification rules
- `app/recommender.py` recommendation engine
- `app/reporter.py` markdown/json outputs
- `app/service.py` orchestration
- `run_once.py` single polling run
- `daemon.py` continuous polling loop

## Usage
```bash
python3 kalshi_mentions_monitor/run_once.py
python3 kalshi_mentions_monitor/daemon.py
```

Environment variables:
- `KALSHI_BASE_URL` (default `https://api.elections.kalshi.com/trade-api/v2`)
- `KALSHI_API_KEY` (optional; currently only attached as a generic auth header if set)
- `KALSHI_POLL_INTERVAL_SECONDS` (default `300`)
- `KALSHI_DB_PATH`
- `KALSHI_OUTPUT_DIR`

## Notes
This project is intentionally rule-based and conservative. It is a prep/recommendation engine, not an execution bot.
