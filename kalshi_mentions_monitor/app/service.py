from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from .classifier import classify_market
from .dashboard import render_dashboard
from .deploy import maybe_deploy_dashboard
from .db import Database
from .event_summary import build_event_summary
from .event_writer import write_event_summary
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

    def _discover_relevant_markets(self) -> tuple[set[str], list]:
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
        return mention_series, markets

    @staticmethod
    def _select_mention_candidates(markets: list, mention_series: set[str]) -> list[tuple]:
        scored = [(m, score_market_for_mentions(m)) for m in markets]
        mention_candidates: list[tuple] = []
        for market, heuristic in scored:
            if market.series_ticker in mention_series:
                heuristic.score += 10
                heuristic.reasons.append('series_ticker contains MENTION')
                heuristic.is_candidate = True
            if heuristic.is_candidate:
                mention_candidates.append((market, heuristic))
        return mention_candidates

    def _analyze_candidates(self, mention_candidates: list[tuple], market_level_errors: list[str]) -> tuple[list[str], list[dict], dict, dict]:
        new_market_ids: list[str] = []
        market_summaries: list[dict] = []
        classifications_by_market: dict = {}
        recommendations_by_market: dict = {}

        for market, heuristic in mention_candidates:
            try:
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
                        'market_id': market.market_id,
                        'title': market.title,
                        'discovery_reason': 'series_ticker contains MENTION',
                        'classification': asdict(classification),
                        'recommendation': asdict(recommendation),
                        'markdown_path': str(md_path),
                        'json_path': str(json_path),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                self.db.log_market_error(market.market_id, 'market_pipeline', str(exc))
                market_level_errors.append(f'market {market.market_id}: {exc}')
        return new_market_ids, market_summaries, classifications_by_market, recommendations_by_market

    def _build_event_outputs(self, markets: list, classifications_by_market: dict, recommendations_by_market: dict, market_level_errors: list[str]) -> list[dict]:
        event_summaries: list[dict] = []
        for group in group_markets(markets):
            try:
                summary = build_event_summary(group, classifications_by_market, recommendations_by_market)
                md_path, json_path = write_event_summary(self.output_dir, summary)
                payload = summary.to_dict() if hasattr(summary, 'to_dict') else dict(summary)
                payload['markdown_path'] = str(md_path)
                payload['json_path'] = str(json_path)
                event_summaries.append(payload)
            except Exception as exc:  # noqa: BLE001
                self.db.log_market_error(group.group_key, 'event_summary', str(exc))
                market_level_errors.append(f'event {group.group_key}: {exc}')
        return event_summaries

    def _render_and_deploy(self) -> tuple[Path, int, dict]:
        dashboard_path, dashboard_events = render_dashboard(self.output_dir)
        deploy_result = maybe_deploy_dashboard(Path(self.output_dir).parent)
        return dashboard_path, dashboard_events, deploy_result

    def run_once(self) -> dict:
        started = datetime.now(UTC).isoformat()
        market_level_errors: list[str] = []

        mention_series, markets = self._discover_relevant_markets()
        mention_candidates = self._select_mention_candidates(markets, mention_series)
        new_market_ids, market_summaries, classifications_by_market, recommendations_by_market = self._analyze_candidates(
            mention_candidates,
            market_level_errors,
        )
        event_summaries = self._build_event_outputs(
            markets,
            classifications_by_market,
            recommendations_by_market,
            market_level_errors,
        )
        dashboard_path, dashboard_events, deploy_result = self._render_and_deploy()

        finished = datetime.now(UTC).isoformat()
        self.db.log_poll_run(
            started,
            finished,
            len(markets),
            len(mention_candidates),
            len(new_market_ids),
            '\n'.join(market_level_errors[:20]),
        )
        return {
            'started_at': started,
            'finished_at': finished,
            'markets_fetched': len(markets),
            'mention_candidates': len(mention_candidates),
            'new_markets_found': len(new_market_ids),
            'market_errors_count': len(market_level_errors),
            'dashboard_path': str(dashboard_path),
            'dashboard_events': dashboard_events,
            'dashboard_deploy': deploy_result,
            'new_markets': market_summaries,
            'event_summaries': event_summaries,
        }
