from __future__ import annotations

from .models import NormalizedMarket
from .strike_intel import strike_display_label

SPEECH_BASELINE_WORDS = {
    'children', 'peace', 'economy / economic', 'safe / safer / safety', 'school',
    'lead / leader / leadership', 'privacy / security', 'history / historic', 'take it down',
}
SPEECH_STRETCH_WORDS = {
    'family', 'families', 'future', 'job', 'jobs', 'youth', 'care', 'protection', 'growth'
}
SPEECH_ODD_WORDS = {'barron', 'chatgpt', 'donald', 'iran', 'ai / artificial intelligence'}


def speech_bucket(label: str) -> str:
    l = (label or '').lower()
    if l == 'event does not qualify':
        return 'nqe'
    if l in SPEECH_BASELINE_WORDS:
        return 'baseline speech'
    if l in SPEECH_ODD_WORDS:
        return 'odd tail'
    if any(x in l for x in SPEECH_STRETCH_WORDS):
        return 'stretch cluster'
    return 'theme-linked'


def apply_speech_basket_logic(market: NormalizedMarket, score: int, reasons: list[str], yes_ref: float | None) -> tuple[int, list[str], str | None, str]:
    label = strike_display_label(market).lower()
    edge_override = None
    strike_type = speech_bucket(label)

    if strike_type == 'nqe':
        score -= 5
        reasons.append('service-only')
        return score, reasons, 'служебный', strike_type

    if strike_type == 'baseline speech':
        score += 3
        reasons.append('baseline basket')
        if yes_ref is not None:
            if yes_ref <= 35:
                score += 2
                reasons.append('cheap')
                edge_override = 'стоит проверить'
            elif yes_ref >= 80:
                score -= 2
                reasons.append('rich exact-token')
                edge_override = 'требует осторожности'
            elif 35 < yes_ref < 75:
                score += 1
                reasons.append('workable price')
        return score, reasons, edge_override, strike_type

    if strike_type == 'stretch cluster':
        score += 1
        reasons.append('theme-adjacent')
        if yes_ref is not None:
            if yes_ref <= 25:
                score += 1
                reasons.append('cheap if theme expands')
            elif yes_ref >= 65:
                score -= 2
                reasons.append('theme > token risk')
                edge_override = 'рынок может переоценивать'
        return score, reasons, edge_override, strike_type

    if strike_type == 'odd tail':
        score -= 3
        reasons.append('odd tail')
        if yes_ref is not None and yes_ref >= 70:
            score -= 2
            reasons.append('rich tail')
            edge_override = 'рынок может переоценивать'
        return score, reasons, edge_override, strike_type

    # theme-linked but not clearly baseline or stretch
    reasons.append('theme-linked')
    if yes_ref is not None:
        if yes_ref <= 20:
            score -= 1
            reasons.append('weak push')
        elif 20 < yes_ref < 60:
            score += 1
            reasons.append('watchlist price')
        elif yes_ref >= 75:
            score -= 1
            reasons.append('rich without baseline')
            edge_override = 'требует осторожности'

    return score, reasons, edge_override, strike_type
