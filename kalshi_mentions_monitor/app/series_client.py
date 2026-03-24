from __future__ import annotations

from typing import Any

import requests


class KalshiSeriesClient:
    def __init__(self, base_url: str, page_limit: int = 1000) -> None:
        self.base_url = base_url.rstrip("/")
        self.page_limit = page_limit

    def fetch_mention_series_tickers(self) -> set[str]:
        response = requests.get(f"{self.base_url}/series", params={"limit": self.page_limit}, timeout=30)
        response.raise_for_status()
        payload = response.json()
        out: set[str] = set()
        for s in payload.get("series", []):
            category = str(s.get("category", "")).lower()
            ticker = str(s.get("ticker", ""))
            title = str(s.get("title", "")).lower()
            if category == "mentions" or "mention" in title or "say" in title or "remarks" in title:
                if ticker:
                    out.add(ticker)
        return out
