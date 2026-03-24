from __future__ import annotations

import json
import time
from datetime import datetime, UTC

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

    while True:
        try:
            result = service.run_once()
            print(json.dumps(result, ensure_ascii=False))
        except Exception as exc:  # noqa: BLE001
            print(json.dumps({
                "time": datetime.now(UTC).isoformat(),
                "error": str(exc),
            }, ensure_ascii=False))
        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()
