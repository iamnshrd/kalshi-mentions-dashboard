from __future__ import annotations

from collections import Counter

from .models import Classification, NormalizedMarket
from .ranking_common import market_yes_reference, price_bucket
from .ranking_general import apply_general_logic
from .ranking_speech import apply_speech_basket_logic
from .ranking_sports import apply_sports_broadcast_logic, sports_bucket
from .strike_intel import strike_display_label, strike_label


def _dedupe_reasons(reasons: list[str]) -> list[str]:
    out = []
    for r in reasons:
        if r and r not in out:
            out.append(r)
    return out[:2]


def _apply_event_composition_adjustments(ranked: list[dict], group_markets: list[NormalizedMarket], event_classification: Classification | None) -> list[dict]:
    if not event_classification or event_classification.market_group != 'sports_announcer_mentions':
        return ranked

    labels = {m.market_id: strike_display_label(m).lower() for m in group_markets}
    bucket_counts = Counter(sports_bucket(label) for label in labels.values())
    structural_live = bucket_counts['review-trigger'] + bucket_counts['injury-contact'] + bucket_counts['play-sequence']
    narrative_total = bucket_counts['narrative-tag']
    weird_total = bucket_counts['weird-tail']

    adjusted = []
    for item in ranked:
        score = item['score']
        reasons = list(item.get('reasons', []))
        label = labels.get(item['market_id'], '')
        bucket = sports_bucket(label)

        if structural_live <= 5 and bucket in {'review-trigger', 'injury-contact', 'play-sequence'}:
            score += 1
            reasons.append('scarce live path')
        if narrative_total >= 4 and bucket == 'narrative-tag':
            score -= 1
            reasons.append('crowded narrative cluster')
            if item['edge_tag'] == 'neutral':
                item['edge_tag'] = 'требует осторожности'
        if weird_total >= 2 and bucket == 'weird-tail':
            score -= 1
            reasons.append('weak tail cluster')
            item['edge_tag'] = 'рынок может переоценивать'

        item = dict(item)
        item['score'] = score
        item['reasons'] = _dedupe_reasons(reasons)
        adjusted.append(item)
    return adjusted


def rank_strikes(group_markets: list[NormalizedMarket], event_classification: Classification | None) -> dict:
    ranked: list[dict] = []
    is_speech_basket = bool(event_classification and event_classification.market_subtype == 'speech' and event_classification.phase_profile == 'opening_heavy')
    is_sports_broadcast = bool(event_classification and event_classification.market_group == 'sports_announcer_mentions')

    for market in group_markets:
        label = strike_label(market.market_id)
        display_label = strike_display_label(market)
        score = 0
        reasons: list[str] = []
        edge = 'neutral'
        strike_type = 'generic'
        yes_ref = market_yes_reference(market)
        bucket = price_bucket(yes_ref)

        if is_speech_basket:
            score, reasons, edge_override, strike_type = apply_speech_basket_logic(market, score, reasons, yes_ref)
            if edge_override is not None:
                edge = edge_override
        elif is_sports_broadcast:
            score, reasons, edge_override, strike_type = apply_sports_broadcast_logic(market, score, reasons, yes_ref)
            if edge_override is not None:
                edge = edge_override
        else:
            score, reasons, strike_type, general_edge = apply_general_logic(market, event_classification, score, reasons, strike_type)
            if general_edge != 'neutral':
                edge = general_edge
            if yes_ref is not None:
                if score >= 3 and yes_ref <= 25:
                    score += 2
                    edge = 'стоит проверить'
                    reasons.append('cheap')
                elif score >= 3 and yes_ref >= 75:
                    score -= 1
                    edge = 'требует осторожности'
                    reasons.append('rich price')
                elif score <= 0 and yes_ref >= 70:
                    score -= 2
                    edge = 'рынок может переоценивать'
                    reasons.append('rich for weak setup')
                elif score <= 0 and yes_ref <= 10:
                    reasons.append('cheap tail')

        if bucket == 'cheap_tail' and event_classification and event_classification.phase_profile in {'qa_heavy', 'mixed'}:
            score += 1
            reasons.append('late-phase optionality')

        if score >= 5 and edge not in {'рынок может переоценивать', 'требует осторожности', 'служебный'}:
            priority_band = 'проверить сначала'
            if edge == 'neutral':
                edge = 'стоит проверить'
        elif score >= 3:
            priority_band = 'проверить после'
            if edge == 'neutral':
                edge = 'рабочая идея'
        elif score >= 1:
            priority_band = 'держать в поле зрения'
            if edge == 'neutral':
                edge = 'погранично'
        else:
            priority_band = 'можно отложить'
            if edge == 'neutral':
                edge = 'пока не приоритет'

        if edge == 'живой, но rules-fragile' and priority_band == 'проверить сначала':
            priority_band = 'проверить после'

        ranked.append({
            'market_id': market.market_id,
            'label': label,
            'display_label': display_label,
            'score': score,
            'priority_band': priority_band,
            'edge_tag': edge,
            'strike_type': strike_type,
            'yes_reference_price': yes_ref,
            'price_bucket': bucket,
            'reasons': _dedupe_reasons(reasons),
        })

    ranked = _apply_event_composition_adjustments(ranked, group_markets, event_classification)
    ranked.sort(key=lambda x: (-x['score'], x['display_label']))

    likely_overreactions = [
        x for x in ranked
        if x['edge_tag'] == 'рынок может переоценивать'
        or ('easy overprice' in x.get('reasons', []))
        or ('headline overread' in x.get('reasons', []))
        or ('rich tail' in x.get('reasons', []))
        or ('rich for weak setup' in x.get('reasons', []))
    ][:5]

    return {
        'top_watchlist': ranked[:5],
        'cheap_watchlist': [x for x in ranked if x['edge_tag'] in {'стоит проверить'}][:5],
        'likely_overreactions': likely_overreactions,
        'low_priority_strikes': [x for x in ranked if x['priority_band'] == 'можно отложить'][:5],
        'full_ranking': ranked,
    }
