from __future__ import annotations

from .models import NormalizedMarket
from .strike_intel import strike_display_label

OVERREACTION_HINTS = [
    'compound', 'hyphen', 'brand', 'service', 'product', 'translated', 'translator', 'specifically advertised',
]
LOW_PRIORITY_HINTS = ['ad', 'advertised', 'sponsor', 'commercial']
EDGE_HINTS = [
    'inflation', 'revenue', 'guidance', 'margin', 'jobs', 'immigration', 'border',
    'tariffs', 'china', 'ukraine', 'israel', 'analyst', 'penalty', 'review', 'injury',
]


def market_yes_reference(market: NormalizedMarket) -> float | None:
    for value in (market.yes_ask, market.yes_price, market.last_price, market.yes_bid):
        if value is not None:
            v = float(value)
            if v <= 1.0:
                v *= 100
            return v
    return None


def price_bucket(yes_ref: float | None) -> str:
    if yes_ref is None:
        return 'unknown'
    if yes_ref <= 15:
        return 'cheap_tail'
    if yes_ref <= 35:
        return 'mid_tail'
    if yes_ref <= 65:
        return 'mid'
    if yes_ref <= 85:
        return 'rich'
    return 'very_rich'


def specific_overreaction_risk(market: NormalizedMarket, speech_baseline_words: set[str] | None = None) -> bool:
    speech_baseline_words = speech_baseline_words or set()
    label = strike_display_label(market).lower()
    text = ' '.join([market.yes_sub_title or '', market.rules_primary or '']).lower()
    if label == 'event does not qualify':
        return True
    if any(h in text for h in OVERREACTION_HINTS):
        return True
    if '/' in label and len(label) > 18 and label not in speech_baseline_words:
        return True
    return False
