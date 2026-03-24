from __future__ import annotations

import json

from app.config import Settings
from app.filtering import score_market_for_mentions
from app.kalshi_client import KalshiClient


def main() -> None:
    settings = Settings()
    client = KalshiClient(settings.base_url, settings.api_key, settings.page_limit, settings.max_pages)
    markets = client.fetch_markets()
    scored = []
    for m in markets:
        r = score_market_for_mentions(m)
        if r.score >= 2:
            scored.append({
                "score": r.score,
                "reasons": r.reasons,
                "ticker": m.market_id,
                "title": m.title,
                "subtitle": m.subtitle,
                "yes_sub_title": m.yes_sub_title,
                "no_sub_title": m.no_sub_title,
                "event_ticker": m.event_ticker,
                "series_ticker": m.series_ticker,
            })
    scored.sort(key=lambda x: x["score"], reverse=True)
    print(json.dumps(scored[:100], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
