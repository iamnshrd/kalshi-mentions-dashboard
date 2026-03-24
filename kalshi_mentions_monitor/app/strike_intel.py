from __future__ import annotations

from .models import Classification, NormalizedMarket

STRUCTURAL_HINTS = [
    'inflation', 'revenue', 'guidance', 'margin', 'rates', 'jobs', 'immigration', 'border'
]
QA_HINTS = [
    'tariffs', 'geopolitical', 'israel', 'terror', 'ukraine', 'china', 'analyst'
]
TRAP_HINTS = [
    'compound', 'exact phrase', 'brand', 'service', 'product'
]


def strike_label(market_id: str) -> str:
    return market_id.rsplit('-', 1)[-1]


def strike_text(m: NormalizedMarket) -> str:
    return ' '.join([
        m.title or '',
        m.subtitle or '',
        m.yes_sub_title or '',
        m.no_sub_title or '',
        m.rules_primary or '',
        m.rules_secondary or '',
    ]).lower()


def classify_strike_bucket(m: NormalizedMarket, event_classification: Classification) -> tuple[str, str]:
    text = strike_text(m)
    label = strike_label(m.market_id)

    if any(h in text for h in TRAP_HINTS):
        return 'likely_trap', f'{label}: elevated wording/rules sensitivity'

    if event_classification.market_group == 'earnings_or_corporate_mentions':
        if any(h in text for h in STRUCTURAL_HINTS):
            return 'structural', f'{label}: likely management-script/core earnings language'
        if any(h in text for h in QA_HINTS):
            return 'qa_sensitive', f'{label}: more likely analyst/Q&A dependent than prepared-remarks dependent'
        return 'contextual', f'{label}: company/event specific; needs quarter-specific context'

    if event_classification.market_group == 'sports_announcer_mentions':
        return 'game_state_sensitive', f'{label}: likely depends on game script, replay, or broadcast flow'

    if event_classification.market_group in {'political_mentions', 'legal_court_mentions'}:
        if any(h in text for h in STRUCTURAL_HINTS):
            return 'structural', f'{label}: likely tied to core event theme or prepared remarks'
        if any(h in text for h in QA_HINTS):
            return 'qa_sensitive', f'{label}: likely more live after opening / in questioning'
        return 'contextual', f'{label}: context-driven strike; current events may dominate history'

    return 'contextual', f'{label}: requires manual review; no strong generic bucket'


def build_strike_intel(group_markets: list[NormalizedMarket], event_classification: Classification) -> dict[str, list[dict[str, str]]]:
    intel: dict[str, list[dict[str, str]]] = {
        'structural': [],
        'qa_sensitive': [],
        'contextual': [],
        'game_state_sensitive': [],
        'likely_trap': [],
    }
    for market in group_markets:
        bucket, note = classify_strike_bucket(market, event_classification)
        intel.setdefault(bucket, []).append({
            'market_id': market.market_id,
            'label': strike_label(market.market_id),
            'note': note,
        })
    return intel
