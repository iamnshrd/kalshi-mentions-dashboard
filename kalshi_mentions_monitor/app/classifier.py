from __future__ import annotations

from .market_features import extract_speaker, infer_event_format, infer_sport, market_text
from .models import Classification, NormalizedMarket


def _extract_features(market: NormalizedMarket) -> dict:
    text = market_text(market)
    return {
        'text': text,
        'event_format': infer_event_format(text),
        'sport': infer_sport(text),
        'speaker': extract_speaker(market.title) or 'unknown',
    }


def _has_any(text: str, needles: list[str]) -> bool:
    return any(x in text for x in needles)


def classify_market(market: NormalizedMarket) -> Classification:
    f = _extract_features(market)
    text = f['text']
    event_format = f['event_format']
    sport = f['sport']
    speaker = f['speaker']

    reasoning: list[str] = []
    group = 'unclear_or_special'
    subtype = 'unknown'
    recurring = 'one_off'
    phase = 'unknown'
    context = 'medium'
    rules_risk = 'low'
    confidence = 0.55
    format_confidence = 0.6

    legal_signals = ['supreme court', 'scotus', 'oral arguments', 'justice', 'hearing', 'testimony', 'committee']
    political_signals = ['trump', 'vance', 'white house', 'senate', 'congress', 'governor', 'president', 'vice president', 'secretary', 'tim walz', 'keir starmer', 'zelenskyy', 'mayor', "mayor's office", 'city hall', 'campaign', 'announcement', 'office announcement', 'press conference', 'press briefing']
    podcast_signals = ['podcast', 'livestream', 'stream', 'spaces', 'youtube live']
    sports_signals = ['the announcers', 'announcers —', 'commentator', 'during the game', 'during the broadcast', 'pregame', 'halftime', 'postgame', 'broadcast crew']
    earnings_signals = ['earnings call', 'investor day', 'guidance', 'ceo', 'cfo', 'quarterly', 'shareholders', 'investor relations']
    entertainment_signals = ['oscars', 'grammys', 'awards', 'ceremony', 'performance', 'host', 'red carpet', 'halftime show', 'during the show']

    if _has_any(text, legal_signals):
        group = 'legal_court_mentions'
        subtype = 'court_hearing' if _has_any(text, ['oral arguments', 'hearing', 'testimony']) else 'legal_remarks'
        recurring = 'semi_recurring'
        phase = 'qa_heavy'
        context = 'high'
        confidence = 0.9
        format_confidence = 0.9
        reasoning.append('Detected legal/court keywords')

    elif _has_any(text, earnings_signals) or event_format == 'earnings_call':
        group = 'earnings_or_corporate_mentions'
        recurring = 'semi_recurring'
        phase = 'mixed'
        context = 'medium'
        confidence = 0.87
        format_confidence = 0.9
        if 'earnings' in text:
            subtype = 'earnings_call'
        elif 'investor day' in text:
            subtype = 'investor_day'
        else:
            subtype = 'corporate_event'
        reasoning.append('Detected corporate/earnings keywords')

    elif _has_any(text, political_signals) or speaker in {'zohran mamdani', 'donald trump', 'melania trump', 'karoline leavitt', 'gavin newsom', 'keir starmer'}:
        group = 'political_mentions'
        recurring = 'semi_recurring'
        context = 'high'
        confidence = 0.88
        format_confidence = 0.85
        reasoning.append('Detected political actor / civic/government format keywords')
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
        elif 'mayor' in text or "mayor's office" in text or 'city hall' in text:
            subtype = 'civic_announcement'
            phase = 'opening_heavy'
        else:
            subtype = 'speech'
            phase = 'opening_heavy'

    elif event_format == 'podcast' or _has_any(text, podcast_signals):
        group = 'culture_entertainment_mentions'
        subtype = 'podcast_or_stream'
        recurring = 'semi_recurring'
        phase = 'mixed'
        context = 'medium'
        confidence = 0.78
        format_confidence = 0.82
        reasoning.append('Detected podcast/stream format')

    elif sport is not None or _has_any(text, sports_signals):
        group = 'sports_announcer_mentions'
        recurring = 'recurring'
        phase = 'game_state_dependent'
        context = 'medium'
        confidence = 0.92
        format_confidence = 0.93
        subtype = f'{sport}_announcer_market' if sport else 'announcer_game_market'
        reasoning.append('Detected sports announcer/broadcast market')

    elif _has_any(text, entertainment_signals):
        group = 'culture_entertainment_mentions'
        recurring = 'one_off'
        phase = 'segment_dependent'
        context = 'high'
        confidence = 0.84
        format_confidence = 0.82
        if _has_any(text, ['awards', 'oscars', 'grammys']):
            subtype = 'awards_broadcast'
        elif _has_any(text, ['performance', 'halftime show']):
            subtype = 'performer_market'
        else:
            subtype = 'live_show'
        reasoning.append('Detected entertainment/culture keywords')

    if 'q&a' in text or 'questions' in text:
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
        speaker=speaker,
        format_confidence=round(max(0.05, min(format_confidence, 0.99)), 2),
        reasoning=reasoning,
    )
