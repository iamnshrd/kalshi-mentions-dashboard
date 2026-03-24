from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, UTC

from .classifier import classify_market
from .db import Database
from .filtering import looks_like_mention_market
from .kalshi_client import KalshiClient
from .recommender import build_recommendation
from .reporter import write_reports


class KalshiMentionMonitorService:
    def __init__(self, client: KalshiClient, db: Database, output_dir):
        self.client = client
        self.db = db
        self.output_dir = output_dir

    def run_once(self) -> dict:
        started = datetime.now(UTC).isoformat()
        markets = self.client.fetch_markets()
        mention_candidates = [m for m in markets if looks_like_mention_market(m)]
        new_market_ids: list[str] = []
        summaries: list[dict] = []

        for market in mention_candidates:
            existed = self.db.market_exists(market.market_id)
            self.db.upsert_market(market)
            if existed:
                continue
            classification = classify_market(market)
            recommendation = build_recommendation(market, classification)
            self.db.upsert_classification(classification)
            self.db.upsert_recommendation(recommendation)
            md_path, json_path = write_reports(self.output_dir, market, classification, recommendation)
            new_market_ids.append(market.market_id)
            summaries.append({
                "market_id": market.market_id,
                "title": market.title,
                "heuristic_score": heuristic.score,
                "heuristic_reasons": heuristic.reasons,
                "classification": asdict(classification),
                "recommendation": asdict(recommendation),
                "markdown_path": str(md_path),
                "json_path": str(json_path),
            })

        finished = datetime.now(UTC).isoformat()
        self.db.log_poll_run(started, finished, len(markets), len(mention_candidates), len(new_market_ids), "")
        return {
            "started_at": started,
            "finished_at": finished,
            "markets_fetched": len(markets),
            "mention_candidates": len(mention_candidates),
            "new_markets_found": len(new_market_ids),
            "new_markets": summaries,
        }
