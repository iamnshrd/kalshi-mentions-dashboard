from __future__ import annotations

from .market_features import infer_event_format, infer_sport, market_text
from .models import Classification, NormalizedMarket


def classify_market(market: NormalizedMarket) -> Classification:
    text = market_text(market)
    reasoning: list[str] = []

    group = 'unclear_or_special'
    subtype = 'unknown'
    recurring = 'one_off'
    phase = 'unknown'
    context = 'medium'
    rules_risk = 'low'
    confidence = 0.55

    event_format = infer_event_format(text)
    sport = infer_sport(text)

    # legal / court first
    if any(x in text for x in ['supreme court', 'scotus', 'oral arguments', 'justice', 'hearing']):
        group = 'legal_court_mentions'
        subtype = 'court_hearing' if 'oral arguments' in text or 'hearing' in text else 'legal_remarks'
        recurring = 'semi_recurring'
        phase = 'qa_heavy'
        context = 'high'
        confidence = 0.9
        reasoning.append('Detected legal/court keywords')

    # political next
    elif any(x in text for x in ['trump', 'vance', 'white house', 'senate', 'congress', 'governor', 'president', 'vice president', 'secretary', 'tim walz', 'keir starmer', 'zelenskyy', 'remarks', 'press conference', 'press briefing']):
        group = 'political_mentions'
        recurring = 'semi_recurring'
        context = 'high'
        confidence = 0.88
        reasoning.append('Detected political actor / format keywords')
        if event_format == 'rally':
            subtype = 'rally'
            phase = 'mixed'
            recurring = 'recurring'
        elif event_format == 'press_conference':
            subtype = 'press_conference'
            phase = 'mixed'
        elif event_format == 'interview':
            subtype = 'interview'
            phase = 'mixed'
        elif event_format == 'hearing':
            subtype = 'hearing'
            phase = 'qa_heavy'
        else:
            subtype = 'speech'
            phase = 'opening_heavy'

    elif sport is not None or any(x in text for x in ['announcer', 'commentator', 'during the game', 'during the broadcast']):
        group = 'sports_announcer_mentions'
        recurring = 'recurring'
        phase = 'game_state_dependent'
        context = 'medium'
        confidence = 0.92
        subtype = f'{sport}_announcer_market' if sport else 'announcer_game_market'
        reasoning.append('Detected sports announcer/broadcast market')

    elif any(x in text for x in ['earnings call', 'investor day', 'guidance', 'ceo', 'cfo', 'quarterly']) or (event_format == 'earnings_call'):
        group = 'earnings_or_corporate_mentions'
        subtype = 'earnings_call' if 'earnings' in text else 'corporate_event'
        recurring = 'semi_recurring'
        phase = 'mixed'
        context = 'medium'
        confidence = 0.87
        reasoning.append('Detected corporate/earnings keywords')

    elif any(x in text for x in ['oscars', 'grammys', 'awards', 'ceremony', 'performance', 'host', 'red carpet', 'halftime show', 'during the show']):
        group = 'culture_entertainment_mentions'
        recurring = 'one_off'
        phase = 'segment_dependent'
        context = 'high'
        confidence = 0.84
        if 'awards' in text or 'oscars' in text or 'grammys' in text:
            subtype = 'awards_broadcast'
        elif 'performance' in text or 'halftime show' in text:
            subtype = 'performer_market'
        else:
            subtype = 'live_show'
        reasoning.append('Detected entertainment/culture keywords')

    if any(x in text for x in ['q&a', 'questions']):
        phase = 'qa_heavy'
        reasoning.append('Q&A-specific phrasing detected')

    if any(x in text for x in ['translator', 'translation', 'translated']):
        rules_risk = 'high'
        confidence -= 0.05
        reasoning.append('Translator risk detected')
    if any(x in text for x in ['brand', 'product', 'service', 'specifically advertised']):
        rules_risk = 'high'
        reasoning.append('Brand/product ambiguity risk detected')
    if any(x in text for x in ['compound', 'hyphen', 'exact phrase']):
        rules_risk = 'medium'
        reasoning.append('Exact wording / morphology sensitivity detected')
    if group == 'unclear_or_special':
        rules_risk = 'medium'
        reasoning.append('Unable to classify confidently; special handling recommended')

    return Classification(
        market_id=market.market_id,
        market_group=group,
        market_subtype=subtype,
        recurring_type=recurring,
        phase_profile=phase,
        context_sensitivity=context,
        rules_risk=rules_risk,
        classification_confidence=round(max(0.05, min(confidence, 0.99)), 2),
        reasoning=reasoning,
    )
