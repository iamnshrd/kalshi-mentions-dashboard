from __future__ import annotations

import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kalshi_mentions_monitor.app.config import Settings
from kalshi_mentions_monitor.app.db import Database
from kalshi_mentions_monitor.app.kalshi_client import KalshiClient
from kalshi_mentions_monitor.app.series_client import KalshiSeriesClient
from kalshi_mentions_monitor.app.service import KalshiMentionMonitorService


def main() -> None:
    settings = Settings()
    settings.ensure_dirs()
    db = Database(settings.db_path)
    client = KalshiClient(settings.base_url, settings.api_key, settings.page_limit, settings.max_pages)
    series_client = KalshiSeriesClient(settings.base_url, settings.page_limit)
    service = KalshiMentionMonitorService(client, series_client, db, settings.output_dir)
    result = service.run_once()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
