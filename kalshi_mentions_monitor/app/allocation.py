from __future__ import annotations

from .analysis_models import StrikeAnalysis
from .models import Classification


def build_event_attention_allocation(classification: Classification | None, market_count: int, rules_risk: str) -> dict:
    if classification is None:
        return {
            'prep_allocation': 'light prep',
            'live_allocation': 'live only',
            'summary': 'Сначала уточни формат события; без этого лучше не тратить много prep-времени.',
        }

    prep = 'light prep'
    live = 'live only'
    summary = 'Достаточно короткой проверки контекста и наблюдения за opening.'

    if classification.market_group in {'political_mentions', 'legal_court_mentions'}:
        prep = 'full prep'
        live = 'full live monitor'
        summary = 'Полезно заранее собрать контекст и быть у экрана с самого начала.'
    elif classification.market_group == 'earnings_or_corporate_mentions':
        prep = 'full prep'
        live = 'phase monitor'
        summary = 'Подготовка особенно важна; в лайве критичен переход prepared remarks → Q&A.'
    elif classification.market_group == 'sports_announcer_mentions':
        prep = 'light prep'
        live = 'full live monitor'
        summary = 'До события достаточно быстро собрать priors, основная работа будет в лайве.'

    if rules_risk == 'high':
        summary += ' Повышенный rules risk: size up без ручной проверки нежелателен.'
    if market_count >= 12:
        summary += ' Страйков много: важно быстро отсеять clutter и не пытаться мониторить всё одинаково.'

    return {
        'prep_allocation': prep,
        'live_allocation': live,
        'summary': summary,
    }


def infer_strike_attention(analysis: StrikeAnalysis, phase_fit: str) -> str:
    edge = analysis.rank.edge_tag
    band = analysis.rank.priority_band
    stype = analysis.rank.strike_type

    if stype == 'nqe':
        return 'pass'
    if edge in {'рынок может переоценивать', 'требует осторожности'}:
        return 'manual only'
    if band == 'проверить сначала':
        return 'core watch'
    if band == 'проверить после':
        return 'secondary watch'
    if phase_fit in {'q&a-heavy', 'game-state-sensitive', 'only-alive-if-topic-breaks'}:
        return 'phase watch'
    if band == 'держать в поле зрения':
        return 'phase watch'
    return 'pass'
