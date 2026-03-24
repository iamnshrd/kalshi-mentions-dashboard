from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    base_url: str = os.getenv("KALSHI_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2")
    api_key: str = os.getenv("KALSHI_API_KEY", "")
    poll_interval_seconds: int = int(os.getenv("KALSHI_POLL_INTERVAL_SECONDS", "300"))
    db_path: Path = Path(os.getenv("KALSHI_DB_PATH", "/root/.openclaw/workspace/kalshi_mentions_monitor/data/kalshi_mentions.db"))
    output_dir: Path = Path(os.getenv("KALSHI_OUTPUT_DIR", "/root/.openclaw/workspace/kalshi_mentions_monitor/output"))
    page_limit: int = int(os.getenv("KALSHI_PAGE_LIMIT", "1000"))
    max_pages: int = int(os.getenv("KALSHI_MAX_PAGES", "10"))

    def ensure_dirs(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "markdown").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "json").mkdir(parents=True, exist_ok=True)
