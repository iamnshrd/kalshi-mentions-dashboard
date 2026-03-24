from __future__ import annotations

from .models import NormalizedMarket
from .strike_intel import strike_display_label

REVIEW_WORDS = {'review', 'challenge', 'flag', 'tech', 'technical'}
INJURY_WORDS = {'injury', 'injured', 'ankle', 'elbow'}
PLAY_WORDS = {'alley-oop', 'airball', 'buzzer', 'overtime', 'triple double'}
ARENA_WORDS = {'crowd', 'crowded', 'american airlines'}
NARRATIVE_WORDS = {'mvp', 'rookie', 'playoff', 'draft', 'jordan'}
WEIRD_TAILS = {'retire / retired / retirement', 'trade / trades / traded', 'event does not qualify'}


def sports_bucket(label: str) -> str:
    l = (label or '').lower()
    if l in WEIRD_TAILS:
        return 'weird-tail'
    if any(x in l for x in REVIEW_WORDS):
        return 'review-trigger'
    if any(x in l for x in INJURY_WORDS):
        return 'injury-contact'
    if any(x in l for x in PLAY_WORDS):
        return 'play-sequence'
    if any(x in l for x in ARENA_WORDS):
        return 'broadcast-filler'
    if any(x in l for x in NARRATIVE_WORDS):
        return 'narrative-tag'
    return 'broadcast-general'


def apply_sports_broadcast_logic(market: NormalizedMarket, score: int, reasons: list[str], yes_ref: float | None) -> tuple[int, list[str], str | None, str]:
    label = strike_display_label(market).lower()
    edge_override = None
    strike_type = sports_bucket(label)

    if strike_type == 'weird-tail':
        score -= 3
        reasons.append('weird tail')
        if yes_ref is not None and yes_ref >= 60:
            score -= 2
            reasons.append('rich tail')
            edge_override = 'рынок может переоценивать'
        return score, reasons, edge_override, 'odd tail'

    if strike_type == 'review-trigger':
        score += 3
        reasons.append('review/whistle trigger')
        if yes_ref is not None:
            if yes_ref <= 35:
                score += 1
                reasons.append('workable price')
            elif yes_ref >= 75:
                score -= 1
                reasons.append('alive but rich')
                edge_override = 'требует осторожности'
        return score, reasons, edge_override, 'game-state'

    if strike_type == 'injury-contact':
        score += 2
        reasons.append('contact/injury path')
        if yes_ref is not None:
            if yes_ref <= 30:
                score += 1
                reasons.append('cheap')
            elif yes_ref >= 70:
                score -= 1
                reasons.append('alive but rich')
                edge_override = 'требует осторожности'
        return score, reasons, edge_override, 'game-state'

    if strike_type == 'play-sequence':
        score += 2
        reasons.append('play-sequence dependent')
        if yes_ref is not None:
            if yes_ref <= 25:
                score += 1
                reasons.append('cheap')
            elif yes_ref >= 80:
                score -= 1
                reasons.append('alive but rich')
                edge_override = 'требует осторожности'
        return score, reasons, edge_override, 'game-state'

    if strike_type == 'broadcast-filler':
        score += 1
        reasons.append('broadcast filler')
        if yes_ref is not None and yes_ref >= 60:
            score -= 2
            reasons.append('easy overprice')
            edge_override = 'рынок может переоценивать'
        return score, reasons, edge_override, 'broadcast-flow'

    if strike_type == 'narrative-tag':
        score += 1
        reasons.append('narrative tag')
        if yes_ref is not None:
            if yes_ref <= 20:
                score += 1
                reasons.append('cheap optionality')
            elif yes_ref >= 65:
                score -= 1
                reasons.append('headline overread')
                edge_override = 'требует осторожности'
        return score, reasons, edge_override, 'broadcast-flow'

    reasons.append('broadcast sensitive')
    if yes_ref is not None:
        if yes_ref <= 20:
            reasons.append('cheap tail')
        elif yes_ref >= 75:
            score -= 1
            reasons.append('rich price')
            edge_override = 'требует осторожности'
    return score, reasons, edge_override, 'broadcast-flow'
