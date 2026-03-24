# Kalshi Mentions Monitor

MVP service that polls Kalshi every 5 minutes, detects new mention-like markets, classifies them, and generates pre-event + live trading recommendations.

## Features
- Polls Kalshi mentions on a fixed cadence
- Detects new markets via SQLite persistence
- Discovers mention markets by `series_ticker` containing `MENTION`
- Filters to markets relevant from today UTC forward
- Applies market classification and recommendation rules
- Generates pre-event, live-trading, and risk-note recommendations
- Writes markdown and JSON summaries for newly discovered markets
- Generates a local HTML dashboard from event summaries
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
python3 kalshi_mentions_monitor/health_check.py
python3 kalshi_mentions_monitor/tests/run_tests.py
python3 kalshi_mentions_monitor/ingest_transcripts.py /path/to/transcripts_dir
# then open:
# /root/.openclaw/workspace/kalshi_mentions_monitor/output/dashboard/index.html
```

## Telegram Mini App
The dashboard build now also produces a Telegram-friendly mobile view:
- Mini App URL: `https://iamnshrd.github.io/kalshi-mentions-dashboard/miniapp/index.html`
- Local file: `/root/.openclaw/workspace/kalshi_mentions_monitor/output/dashboard/miniapp/index.html`

To wire it into a Telegram bot:

```bash
export TELEGRAM_BOT_TOKEN='...'
export TELEGRAM_MINIAPP_URL='https://iamnshrd.github.io/kalshi-mentions-dashboard/miniapp/index.html'

# set bot menu button
python3 kalshi_mentions_monitor/telegram_set_menu_button.py

# send a one-off launch button into a chat
python3 kalshi_mentions_monitor/telegram_send_miniapp_button.py <chat_id> 'Открыть Mentions Mini App'
```

You can also configure the same menu button manually in BotFather via `/setmenubutton`.

## V1 scope
See `V1_SCOPE.md` for the current V1 boundary / freeze criteria.

Environment variables:
- `KALSHI_BASE_URL` (default `https://api.elections.kalshi.com/trade-api/v2`)
- `KALSHI_API_KEY` (optional; currently only attached as a generic auth header if set)
- `KALSHI_POLL_INTERVAL_SECONDS` (default `300`)
- `KALSHI_DB_PATH`
- `KALSHI_OUTPUT_DIR`

## Notes
Discovery is intentionally simple and robust: a market is considered a mention market if its `series_ticker` contains `MENTION`.
The monitor then filters to markets dated from today UTC forward using market timestamps and ticker/event date hints.

This project is intentionally rule-based and conservative. It is a prep/recommendation engine, not an execution bot.
