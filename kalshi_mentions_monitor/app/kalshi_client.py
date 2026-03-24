from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests

from .models import NormalizedMarket


class KalshiClient:
    def __init__(self, base_url: str, api_key: str = "", page_limit: int = 1000, max_pages: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.page_limit = page_limit
        self.max_pages = max_pages

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key
        return headers

    def fetch_markets(self) -> list[NormalizedMarket]:
        cursor = None
        all_markets: list[NormalizedMarket] = []
        for _ in range(self.max_pages):
            params: dict[str, Any] = {"limit": self.page_limit}
            if cursor:
                params["cursor"] = cursor
            response = requests.get(f"{self.base_url}/markets", params=params, headers=self._headers(), timeout=30)
            response.raise_for_status()
            payload = response.json()
            for raw in payload.get("markets", []):
                all_markets.append(self._normalize_market(raw))
            cursor = payload.get("cursor")
            if not cursor:
                break
        return all_markets

    def fetch_markets_for_series(self, series_ticker: str) -> list[NormalizedMarket]:
        response = requests.get(
            f"{self.base_url}/markets",
            params={"limit": 200, "series_ticker": series_ticker},
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return [self._normalize_market(raw) for raw in payload.get("markets", [])]

    def fetch_markets_for_series_bulk(self, series_tickers: set[str], max_workers: int = 24) -> list[NormalizedMarket]:
        out: list[NormalizedMarket] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.fetch_markets_for_series, ticker): ticker for ticker in sorted(series_tickers)}
            for future in as_completed(futures):
                try:
                    out.extend(future.result())
                except Exception:
                    continue
        return out

    @staticmethod
    def _normalize_market(raw: dict[str, Any]) -> NormalizedMarket:
        return NormalizedMarket(
            market_id=raw.get("ticker", ""),
            event_ticker=raw.get("event_ticker", ""),
            ticker=raw.get("ticker", ""),
            title=raw.get("title", "") or "",
            subtitle=raw.get("subtitle", "") or "",
            yes_sub_title=raw.get("yes_sub_title", "") or "",
            no_sub_title=raw.get("no_sub_title", "") or "",
            rules_primary=raw.get("rules_primary", "") or "",
            rules_secondary=raw.get("rules_secondary", "") or "",
            status=raw.get("status", "") or "",
            market_type=raw.get("market_type", "") or "",
            series_ticker=raw.get("series_ticker", "") or "",
            open_time=raw.get("open_time", "") or "",
            close_time=raw.get("close_time", "") or "",
            created_time=raw.get("created_time", "") or "",
            updated_time=raw.get("updated_time", "") or "",
            raw_json=raw,
        )
