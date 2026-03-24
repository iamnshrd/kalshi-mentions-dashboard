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
            ticker = str(s.get("ticker", ""))
            if ticker and "MENTION" in ticker.upper():
                out.add(ticker)
        return out
