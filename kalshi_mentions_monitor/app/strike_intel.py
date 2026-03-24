from __future__ import annotations

import re

from .grouping import EventGroup
from .models import Classification, NormalizedMarket


STRUCTURAL_HINTS = ['inflation', 'revenue', 'guidance', 'margin', 'rates', 'jobs', 'immigration', 'border']
QA_HINTS = ['tariffs', 'geopolitical', 'israel', 'terror', 'ukraine', 'china', 'analyst']
TRAP_HINTS = ['compound', 'exact phrase', 'brand', 'service', 'product']


def _strike_label(market_id: str) -> str:
    return market_id.rsplit('-', 1)[-1]


def _strike_text(m: NormalizedMarket) -> str:
    return ' '.join([m.title, m.subtitle, m.yes_sub_title, m.no_sub_title, m.rules_primary, m.rules_secondary]).lower()


def classify_strike_bucket(m: NormalizedMarket, event_classification: Classification) -> tuple[str, str]:
    text = _strike_text(m)
    label = _strike_label(m.market_id)

    if any(h in text for h in TRAP_HINTS):
        return 'likely_trap', f'{label}: wording/rules sensitivity elevated'

    if event_classification.market_group == 'earnings_or_corporate_mentions':
        if any(h in text for h in STRUCTURAL_HINTS):
            return 'structural', f'{label}: likely management-script/core earnings language'
        if any(h in text for h in QA_HINTS):
            return 'qa_sensitive', f'{label}: more likely analyst/Q&A dependent than prepared-remarks dependent'
        return 'contextual', f'{label}: company/event specific; needs quarter-specific context'

    if event_classification.market_group == 'sports_announcer_mentions':
        if any(x in text for x in ['announcers say during', 'during the game']):
            return 'game_state_sensitive', f'{label}: likely depends on game script, replay, or broadcast sequence'
        return 'contextual', f'{label}: likely tied to game context rather than pure baseline frequency'

    if event_classification.market_group in {'political_mentions', 'legal_court_mentions'}:
        if any(h in text for h in STRUCTURAL_HINTS):
            return 'structural', f'{label}: likely tied to core event theme or expected prepared remarks'
        if any(h in text for h in QA_HINTS):
            return 'qa_sensitive', f'{label}: likely to matter more after opening / in questions or adversarial follow-up'
        return 'contextual', f'{label}: context-driven strike; current events may dominate history'

    return 'contextual', f'{label}: requires manual review; no strong generic bucket'


def build_strike_intel(group: EventGroup, classifications: dict[str, Classification]) -> dict:
    intel = {
        'structural': [],
        'qa_sensitive': [],
        'contextual': [],
        'likely_trap': [],
        'game_state_sensitive': [],
    }

    dominant = classifications.get(group.markets[0].market_id)
    if dominant is None:
        return intel

    for m in group.markets:
        bucket, note = classify_strike_bucket(m, dominant)
        intel.setdefault(bucket, []).append({
            'market_id': m.market_id,
            'label': _strike_label(m.market_id),
            'note': note,
        })
    return intel
