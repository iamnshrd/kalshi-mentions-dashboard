from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime

from .classifier import classify_market
from .db import Database
from .event_summary import build_event_summary, write_event_summary
from .filtering import score_market_for_mentions
from .grouping import group_markets
from .kalshi_client import KalshiClient
from .recommender import build_recommendation
from .reporter import write_reports
from .series_client import KalshiSeriesClient
from .time_filter import is_relevant_from_date, today_utc


class KalshiMentionMonitorService:
    def __init__(self, client: KalshiClient, series_client: KalshiSeriesClient, db: Database, output_dir):
        self.client = client
        self.series_client = series_client
        self.db = db
        self.output_dir = output_dir

    def run_once(self) -> dict:
        started = datetime.now(UTC).isoformat()
        mention_series = self.series_client.fetch_mention_series_tickers()

        markets = []
        seen_ids: set[str] = set()
        from_date = today_utc()
        for market in self.client.fetch_markets_for_series_bulk(mention_series):
            if market.market_id in seen_ids:
                continue
            seen_ids.add(market.market_id)
            if is_relevant_from_date(market, from_date):
                markets.append(market)

        scored = [(m, score_market_for_mentions(m)) for m in markets]
        mention_candidates: list[tuple] = []
        for market, heuristic in scored:
            if market.series_ticker in mention_series:
                heuristic.score += 10
                heuristic.reasons.append("series_ticker contains MENTION")
                heuristic.is_candidate = True
            if heuristic.is_candidate:
                mention_candidates.append((market, heuristic))

        new_market_ids: list[str] = []
        market_summaries: list[dict] = []
        classifications_by_market = {}
        recommendations_by_market = {}

        for market, heuristic in mention_candidates:
            existed = self.db.market_exists(market.market_id)
            self.db.upsert_market(market)

            classification = classify_market(market)
            recommendation = build_recommendation(market, classification)
            self.db.upsert_classification(classification)
            self.db.upsert_recommendation(recommendation)
            classifications_by_market[market.market_id] = classification
            recommendations_by_market[market.market_id] = recommendation

            if existed:
                continue

            md_path, json_path = write_reports(self.output_dir, market, classification, recommendation)
            new_market_ids.append(market.market_id)
            market_summaries.append(
                {
                    "market_id": market.market_id,
                    "title": market.title,
                    "discovery_reason": "series_ticker contains MENTION",
                    "classification": asdict(classification),
                    "recommendation": asdict(recommendation),
                    "markdown_path": str(md_path),
                    "json_path": str(json_path),
                }
            )

        event_summaries: list[dict] = []
        for group in group_markets(markets):
            summary = build_event_summary(group, classifications_by_market, recommendations_by_market)
            md_path, json_path = write_event_summary(self.output_dir, summary)
            summary["markdown_path"] = str(md_path)
            summary["json_path"] = str(json_path)
            event_summaries.append(summary)

        finished = datetime.now(UTC).isoformat()
        self.db.log_poll_run(started, finished, len(markets), len(mention_candidates), len(new_market_ids), "")
        return {
            "started_at": started,
            "finished_at": finished,
            "markets_fetched": len(markets),
            "mention_candidates": len(mention_candidates),
            "new_markets_found": len(new_market_ids),
            "new_markets": market_summaries,
            "event_summaries": event_summaries,
        }
