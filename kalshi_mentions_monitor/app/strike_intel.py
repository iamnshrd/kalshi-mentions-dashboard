from __future__ import annotations

from .models import Classification, NormalizedMarket

STRUCTURAL_HINTS = [
    'inflation', 'revenue', 'guidance', 'margin', 'rates', 'jobs', 'immigration', 'border'
]
QA_HINTS = [
    'tariffs', 'geopolitical', 'israel', 'terror', 'ukraine', 'china', 'analyst'
]
TRAP_HINTS = [
    'compound', 'hyphen', 'brand', 'service', 'product', 'specifically advertised', 'translator', 'translated'
]


def strike_label(market_id: str) -> str:
    return market_id.rsplit('-', 1)[-1]


def strike_display_label(m: NormalizedMarket) -> str:
    for value in (m.yes_sub_title, m.no_sub_title, m.subtitle):
        if value and str(value).strip():
            return str(value).strip()
    return strike_label(m.market_id)


def strike_text(m: NormalizedMarket) -> str:
    return ' '.join([
        m.title or '',
        m.subtitle or '',
        m.yes_sub_title or '',
        m.no_sub_title or '',
        m.rules_primary or '',
        m.rules_secondary or '',
    ]).lower()


def _specific_trap(m: NormalizedMarket) -> bool:
    text = ' '.join([
        m.yes_sub_title or '',
        m.no_sub_title or '',
        m.rules_primary or '',
    ]).lower()
    label = strike_display_label(m).lower()

    if label == 'event does not qualify':
        return True
    if any(h in text for h in TRAP_HINTS):
        return True
    if '/' in label and len(label) > 18:
        return True
    return False


def _phase_tag(bucket: str, base_note: str, event_classification: Classification, label: str) -> str:
    if bucket == 'likely_trap':
        return 'rules'
    if bucket == 'game_state_sensitive':
        return 'live'
    if bucket == 'qa_sensitive':
        return 'q&a'
    if bucket == 'structural':
        return 'opening'
    if 'theme bridge' in base_note or 'context-dependent' in base_note:
        return 'pivot'
    if 'name-only' in base_note or 'rhetorical' in base_note:
        return 'tail'
    if 'social/family' in base_note:
        return 'theme'
    if event_classification.market_group == 'earnings_or_corporate_mentions':
        return 'context'
    return 'mixed'


def classify_strike_bucket(m: NormalizedMarket, event_classification: Classification) -> tuple[str, str]:
    text = strike_text(m)
    label = strike_display_label(m).lower()

    if _specific_trap(m):
        base_note = 'special-rule / exact-token risk'
        return 'likely_trap', f"{base_note} · {_phase_tag('likely_trap', base_note, event_classification, label)}"

    if event_classification.market_subtype == 'podcast_or_stream':
        if any(x in label for x in ['huberman', 'sleep', 'silicon valley', 'crypto', 'startup', 'supplement', 'longevity']):
            base_note = 'host-chemistry lane'
            return 'contextual', f"{base_note} · pivot"
        if any(x in label for x in ['election', 'ukraine', 'war', 'inflation', 'fed']):
            base_note = 'forced topical pivot'
            return 'qa_sensitive', f"{base_note} · q&a"
        if any(x in label for x in ['wolverine', 'meme', 'joke']):
            base_note = 'banter tail'
            return 'contextual', f"{base_note} · tail"
        base_note = 'conversation-dependent token'
        return 'contextual', f"{base_note} · mixed"

    if event_classification.market_group == 'earnings_or_corporate_mentions':
        if any(h in text for h in STRUCTURAL_HINTS) or any(x in label for x in ['guidance', 'margin', 'revenue', 'sales', 'eps']):
            base_note = 'prepared-remarks relevant'
            return 'structural', f"{base_note} · {_phase_tag('structural', base_note, event_classification, label)}"
        if any(h in text for h in QA_HINTS):
            base_note = 'Q&A-leaning'
            return 'qa_sensitive', f"{base_note} · {_phase_tag('qa_sensitive', base_note, event_classification, label)}"
        base_note = 'needs quarter-specific context'
        return 'contextual', f"{base_note} · {_phase_tag('contextual', base_note, event_classification, label)}"

    if event_classification.market_group == 'sports_announcer_mentions':
        if any(x in label for x in ['tech', 'technical', 'review', 'challenge', 'flag']):
            base_note = 'review/whistle trigger'
            return 'game_state_sensitive', f"{base_note} · live"
        if any(x in label for x in ['injury', 'injured', 'ankle', 'elbow']):
            base_note = 'contact/injury path'
            return 'game_state_sensitive', f"{base_note} · live"
        if any(x in label for x in ['alley-oop', 'airball', 'buzzer', 'overtime', 'triple double']):
            base_note = 'play-sequence dependent'
            return 'game_state_sensitive', f"{base_note} · live"
        if any(x in label for x in ['crowd', 'american airlines']):
            base_note = 'broadcast filler'
            return 'game_state_sensitive', f"{base_note} · tail"
        if any(x in label for x in ['mvp', 'rookie', 'playoff', 'draft', 'jordan']):
            base_note = 'narrative tag'
            return 'game_state_sensitive', f"{base_note} · tail"
        base_note = 'broadcast-flow dependent'
        return 'game_state_sensitive', f"{base_note} · live"

    if event_classification.market_group in {'political_mentions', 'legal_court_mentions'}:
        if event_classification.market_subtype == 'civic_announcement':
            if any(x in label for x in ['budget', 'housing', 'rent', 'afford', 'school', 'education', 'nypd', 'subway', 'tax', 'crime']):
                base_note = 'local governance lane'
                return 'contextual', f"{base_note} · opening"
            if any(x in label for x in ['governor', 'hochul', 'credit', 'laguardia']):
                base_note = 'office-framing dependent'
                return 'contextual', f"{base_note} · pivot"
            if any(x in label for x in ['trump', 'biden', 'donald', 'president']):
                base_note = 'national-politics tail'
                return 'contextual', f"{base_note} · tail"
            if any(x in label for x in ['iran', 'israel', 'ukraine', 'war', 'peace']):
                base_note = 'geo tail for civic event'
                return 'qa_sensitive', f"{base_note} · q&a"
            if any(x in label for x in ['muslim', 'ramadan']):
                base_note = 'identity/community lane'
                return 'contextual', f"{base_note} · pivot"
            base_note = 'civic-context dependent'
            return 'contextual', f"{base_note} · mixed"
        if any(h in text for h in STRUCTURAL_HINTS):
            base_note = 'opening-relevant core theme'
            return 'structural', f"{base_note} · {_phase_tag('structural', base_note, event_classification, label)}"
        if any(h in text for h in QA_HINTS):
            base_note = 'needs Q&A / topic pivot'
            return 'qa_sensitive', f"{base_note} · {_phase_tag('qa_sensitive', base_note, event_classification, label)}"
        if any(x in label for x in ['children', 'family', 'families', 'education', 'school', 'youth']):
            base_note = 'social/family lane only'
            return 'contextual', f"{base_note} · {_phase_tag('contextual', base_note, event_classification, label)}"
        if any(x in label for x in ['economy', 'economic', 'jobs', 'prices', 'inflation', 'tariffs', 'border', 'immigration']):
            base_note = 'macro-policy lane'
            return 'structural', f"{base_note} · {_phase_tag('structural', base_note, event_classification, label)}"
        if any(x in label for x in ['peace', 'war', 'iran', 'israel', 'ukraine', 'security', 'privacy']):
            base_note = 'geo/conflict dependent'
            return 'qa_sensitive', f"{base_note} · {_phase_tag('qa_sensitive', base_note, event_classification, label)}"
        if any(x in label for x in ['chatgpt', 'ai', 'technology', 'tech']):
            base_note = 'theme bridge required'
            return 'contextual', f"{base_note} · {_phase_tag('contextual', base_note, event_classification, label)}"
        if any(x in label for x in ['donald', 'barron', 'melania', 'ivanka', 'trump']):
            base_note = 'name-only exposure'
            return 'contextual', f"{base_note} · {_phase_tag('contextual', base_note, event_classification, label)}"
        if any(x in label for x in ['history', 'historic', 'future', 'freedom', 'america', 'greatness']):
            base_note = 'rhetorical token'
            return 'contextual', f"{base_note} · {_phase_tag('contextual', base_note, event_classification, label)}"
        base_note = 'context-dependent token'
        return 'contextual', f"{base_note} · {_phase_tag('contextual', base_note, event_classification, label)}"

    base_note = 'manual review'
    return 'contextual', f"{base_note} · {_phase_tag('contextual', base_note, event_classification, label)}"


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
            'label': strike_display_label(market),
            'short_label': strike_label(market.market_id),
            'note': note,
        })
    return intel
