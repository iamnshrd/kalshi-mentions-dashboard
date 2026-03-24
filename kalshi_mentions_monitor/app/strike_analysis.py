from __future__ import annotations

from .analysis_models import StrikeAnalysis
from .models import Classification, NormalizedMarket
from .presentation import enrich_rank_item
from .strike_intel import classify_strike_bucket, strike_display_label, strike_label
from .strike_priority import rank_strikes


def build_strike_analyses(group_markets: list[NormalizedMarket], event_classification: Classification | None) -> tuple[list[StrikeAnalysis], dict, dict]:
    ranked_payload = rank_strikes(group_markets, event_classification)
    rank_by_id = {item['market_id']: enrich_rank_item(item) for item in ranked_payload['full_ranking']}

    analyses: list[StrikeAnalysis] = []
    intel: dict[str, list[dict]] = {
        'structural': [],
        'qa_sensitive': [],
        'contextual': [],
        'game_state_sensitive': [],
        'likely_trap': [],
    }

    for market in group_markets:
        label = strike_display_label(market)
        short = strike_label(market.market_id)
        if event_classification is not None:
            bucket, note = classify_strike_bucket(market, event_classification)
        else:
            bucket, note = 'contextual', f'{label}: нужен ручной разбор; нет классификации события'
        rank = rank_by_id[market.market_id]
        analysis = StrikeAnalysis(
            market_id=market.market_id,
            label=label,
            short_label=short,
            note=note,
            bucket=bucket,
            rank=rank,
        )
        analyses.append(analysis)
        intel.setdefault(bucket, []).append({
            'market_id': market.market_id,
            'label': label,
            'short_label': short,
            'note': note,
        })

    strike_priority = {
        key: [rank_by_id[item['market_id']].to_dict() for item in value]
        for key, value in {
            'top_watchlist': ranked_payload['top_watchlist'],
            'cheap_watchlist': ranked_payload['cheap_watchlist'],
            'likely_overreactions': ranked_payload['likely_overreactions'],
            'low_priority_strikes': ranked_payload['low_priority_strikes'],
            'full_ranking': ranked_payload['full_ranking'],
        }.items()
    }
    return analyses, intel, strike_priority
