from __future__ import annotations

from .models import Classification, NormalizedMarket
from .ranking_common import EDGE_HINTS, LOW_PRIORITY_HINTS, specific_overreaction_risk
from .strike_intel import strike_display_label, strike_text


def apply_general_logic(market: NormalizedMarket, event_classification: Classification | None, score: int, reasons: list[str], strike_type: str) -> tuple[int, list[str], str, str]:
    text = strike_text(market)
    label = strike_display_label(market).lower()
    edge = 'neutral'

    if event_classification is not None:
        if event_classification.market_group in {'political_mentions', 'legal_court_mentions'}:
            if event_classification.market_subtype == 'civic_announcement':
                if any(h in label for h in ['budget', 'housing', 'rent', 'afford', 'school', 'education', 'nypd', 'subway', 'tax', 'crime']):
                    score += 3
                    reasons.append('local governance lane')
                    strike_type = 'theme-linked' if strike_type == 'generic' else strike_type
                elif any(h in label for h in ['governor', 'hochul', 'credit', 'laguardia']):
                    score += 1
                    reasons.append('office-framing dependent')
                    strike_type = 'theme-linked' if strike_type == 'generic' else strike_type
                elif any(h in label for h in ['muslim', 'ramadan']):
                    score += 1
                    reasons.append('identity/community lane')
                    strike_type = 'theme-linked' if strike_type == 'generic' else strike_type
                elif any(h in label for h in ['trump', 'biden', 'ukraine', 'israel', 'iran', 'china', 'ai', 'chatgpt', 'president']):
                    score -= 2
                    reasons.append('national-politics tail')
                    strike_type = 'odd tail' if strike_type == 'generic' else strike_type
                else:
                    score += 0
                    reasons.append('civic-context dependent')
                    strike_type = 'theme-linked' if strike_type == 'generic' else strike_type
            else:
                if any(h in text for h in ['immigration', 'border', 'jobs', 'tariffs', 'china', 'ukraine', 'israel']):
                    score += 2
                    reasons.append('current-events lane')
                    if strike_type == 'generic':
                        strike_type = 'theme-linked'
                if 'q&a' in text or 'questions' in text or 'analyst' in text:
                    score += 2
                    reasons.append('question-driven')
                    strike_type = 'qa-sensitive'
                if event_classification.phase_profile in {'opening_heavy', 'mixed'}:
                    score += 1
                    reasons.append('opening-relevant')

        elif event_classification.market_group == 'earnings_or_corporate_mentions':
            if any(h in text for h in ['guidance', 'revenue', 'margin', 'quarterly', 'analyst']):
                score += 3
                reasons.append('prepared-vs-q&a split')
                strike_type = 'theme-linked'

        elif event_classification.market_group == 'culture_entertainment_mentions' and event_classification.market_subtype == 'podcast_or_stream':
            if any(h in label for h in ['sleep', 'huberman', 'silicon valley', 'startup', 'crypto', 'drug', 'supplement', 'longevity']):
                score += 3
                reasons.append('host-chemistry lane')
                strike_type = 'theme-linked' if strike_type == 'generic' else strike_type
            elif any(h in label for h in ['election', 'ukraine', 'war', 'inflation', 'fed']):
                score -= 2
                reasons.append('forced topical pivot')
                strike_type = 'odd tail' if strike_type == 'generic' else strike_type
            elif any(h in label for h in ['wolverine', 'meme', 'joke']):
                score -= 1
                reasons.append('banter tail')
                strike_type = 'odd tail' if strike_type == 'generic' else strike_type
            else:
                score += 1
                reasons.append('conversation-flow dependent')
                strike_type = 'theme-linked' if strike_type == 'generic' else strike_type

        elif event_classification.market_group == 'sports_announcer_mentions':
            if any(h in text for h in ['penalty', 'review', 'injury', 'replay', 'challenge', 'flag']):
                score += 3
                reasons.append('game-state trigger')
                strike_type = 'game-state'
            elif any(h in label for h in ['crowd', 'coach', 'bench', 'timeout', 'halftime', 'buzzer']):
                score += 2
                reasons.append('broadcast-flow fit')
                strike_type = 'broadcast-flow'
            else:
                score += 1
                reasons.append('broadcast sensitive')
                strike_type = 'broadcast-flow'

    if any(h in text for h in EDGE_HINTS):
        score += 1
        if strike_type == 'generic':
            strike_type = 'theme-linked'
    if specific_overreaction_risk(market):
        score -= 1
        reasons.append('rules / wording risk')
        if score >= 2:
            edge = 'живой, но rules-fragile'
        else:
            edge = 'осторожно'
        if strike_type == 'generic':
            strike_type = 'special rule'
    if any(h in label for h in LOW_PRIORITY_HINTS):
        score -= 2
        reasons.append('weak setup')
        strike_type = 'odd tail'

    return score, reasons, strike_type, edge
