from __future__ import annotations

import json
from pathlib import Path

from app.config import Settings
from app.db import Database
from app.kalshi_client import KalshiClient
from app.service import KalshiMentionMonitorService
from app.series_client import KalshiSeriesClient


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
