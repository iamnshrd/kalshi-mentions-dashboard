from __future__ import annotations

from collections import Counter
from pathlib import Path

from .allocation import build_event_attention_allocation, infer_strike_attention
from .analysis_models import EventAnalysis
from .analytics_helpers import (
    build_consensus_misread_notes,
    build_relevant_history_notes,
    build_semantic_families,
    infer_phase_fit,
)
from .config import Settings
from .context_enrichment import build_context_enrichment
from .current_context import build_current_context_signals
from .current_news import build_news_context_notes
from .grouping import EventGroup
from .live_plan import build_live_plan
from .models import Classification, Recommendation
from .strike_analysis import build_strike_analyses
from .strike_intel import strike_display_label
# from .transcript_lookup import lookup_relevant_transcripts  # frozen for now; transcript layer is not a current priority


def build_event_summary(group: EventGroup, classifications: dict[str, Classification], recommendations: dict[str, Recommendation]) -> EventAnalysis:
    class_counter: Counter[str] = Counter()
    subtype_counter: Counter[str] = Counter()
    rules_counter: Counter[str] = Counter()
    for market in group.markets:
        c = classifications.get(market.market_id)
        if not c:
            continue
        class_counter[c.market_group] += 1
        subtype_counter[c.market_subtype] += 1
        rules_counter[c.rules_risk] += 1

    dominant_group = class_counter.most_common(1)[0][0] if class_counter else 'unclear_or_special'
    dominant_subtype = subtype_counter.most_common(1)[0][0] if subtype_counter else 'unknown'
    dominant_rules_risk = rules_counter.most_common(1)[0][0] if rules_counter else 'medium'
    speakers = [classifications[m.market_id].speaker for m in group.markets if m.market_id in classifications and classifications[m.market_id].speaker != 'unknown']
    speaker = speakers[0] if speakers else 'unknown'
    format_confidence = max([classifications[m.market_id].format_confidence for m in group.markets if m.market_id in classifications] or [0.5])

    pre: list[str] = []
    live: list[str] = []
    risk: list[str] = []
    for market in group.markets[:5]:
        rec = recommendations.get(market.market_id)
        if not rec:
            continue
        pre.extend(rec.pre_event_recommendations[:2])
        live.extend(rec.live_trading_recommendations[:2])
        risk.extend(rec.risk_notes[:2])

    def dedupe(xs: list[str]) -> list[str]:
        out, seen = [], set()
        for x in xs:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    if dominant_group == 'sports_announcer_mentions':
        prep_focus = 'Собери priors по комментаторам, сети и game state ещё до открытия рынка.'
        live_focus = 'Следи за тем, как игра и эфирный flow меняют релевантность страйков.'
        priority = 'high'
    elif dominant_group == 'earnings_or_corporate_mentions':
        prep_focus = 'Раздели prepared remarks и analyst Q&A ещё до события.'
        live_focus = 'После prepared remarks быстро пересмотри Q&A-heavy страйки.'
        priority = 'normal'
    elif dominant_group == 'legal_court_mentions':
        prep_focus = 'Сначала подтверди, кто именно должен сказать фразу и что считается по rules.'
        live_focus = 'Следи за speaker identity и логикой hearing/oral arguments, а не за случайными словами.'
        priority = 'high'
    elif dominant_group == 'political_mentions' and dominant_subtype == 'civic_announcement':
        prep_focus = 'Пойми официальный повод, local news context и ожидаемый office framing до открытия.'
        live_focus = 'Смотри, остаётся ли спикер в узком civic/office framing или уходит в broader political narrative.'
        priority = 'high'
    elif dominant_group == 'culture_entertainment_mentions' and dominant_subtype == 'podcast_or_stream':
        prep_focus = 'Пойми формат подкаста, co-host dynamic и какие темы реально могут organically зайти в разговор.'
        live_focus = 'Следи за topic drift, banter flow и guest/host pivots, а не за scripted-opening логикой.'
        priority = 'normal'
    else:
        prep_focus = 'Собери контекст, формат события и кластеры страйков перед торговлей.'
        live_focus = 'Используй opening как быстрый тест того, какой narrative cluster реально живёт.'
        priority = 'high' if dominant_group == 'political_mentions' else 'normal'
    if dominant_rules_risk == 'high':
        priority = 'normal'

    strike_codes = [strike_display_label(m) for m in group.markets]
    strike_buckets = {'count': len(strike_codes), 'context_sensitive_hint': len([x for x in strike_codes if x])}
    first_classification = classifications.get(group.markets[0].market_id) if group.markets else None
    context = build_context_enrichment(group.event_title, first_classification) if first_classification else {'context_checks': [], 'likely_hooks': [], 'context_notes': []}
    live_plan = build_live_plan(first_classification) if first_classification else {'opening_plan': [], 'post_opening_plan': [], 'qa_transition_plan': []}
    strike_analyses, strike_intel, strike_priority = build_strike_analyses(group.markets, first_classification)
    current_context = build_current_context_signals(group.event_title, first_classification, strike_analyses) if first_classification else {'signals': [], 'hooks': [], 'notes': []}
    current_news = build_news_context_notes(group.event_title, first_classification) if first_classification and priority == 'high' else {'checks': [], 'hooks': [], 'notes': []}

    relevant_history_notes = build_relevant_history_notes(first_classification, group.event_title, strike_analyses)
    consensus_misread = build_consensus_misread_notes(first_classification, group.event_title, strike_analyses)
    semantic_families = build_semantic_families(first_classification, strike_analyses)
    attention_allocation = build_event_attention_allocation(first_classification, len(group.markets), dominant_rules_risk)
    settings = Settings()
    # transcript_matches = lookup_relevant_transcripts(settings.db_path, group.event_title, first_classification, speaker, limit=5)
    transcript_matches: list[dict] = []

    strike_analyses_payload = []
    for analysis in strike_analyses:
        data = analysis.to_dict()
        phase_fit = infer_phase_fit(first_classification, analysis)
        data['phase_fit'] = phase_fit
        data['attention_allocation'] = infer_strike_attention(analysis, phase_fit)
        strike_analyses_payload.append(data)

    manual_trader_prompts = dedupe([
        *context['context_checks'][:3],
        *live_plan['opening_plan'][:2],
        *live_plan['qa_transition_plan'][:2],
        'Проверь, не переоценивает ли рынок headline topic вместо exact token или event phase.',
        'Отдели baseline basket words от odd tails и rules-sensitive страйков перед тем как size up.',
    ])[:8]

    return EventAnalysis(
        group_key=group.group_key,
        event_title=group.event_title,
        event_ticker=group.event_ticker,
        series_ticker=group.series_ticker,
        status=group.status,
        open_time=group.open_time,
        close_time=group.close_time,
        market_count=len(group.markets),
        dominant_group=dominant_group,
        dominant_subtype=dominant_subtype,
        dominant_rules_risk=dominant_rules_risk,
        speaker=speaker,
        format_confidence=round(format_confidence, 2),
        prep_focus=prep_focus,
        live_focus=live_focus,
        priority=priority,
        strike_codes=strike_codes,
        strike_buckets=strike_buckets,
        strike_intel=strike_intel,
        strike_analyses=strike_analyses_payload,
        context_checks=(context['context_checks'] + current_context['signals'] + current_news['checks'])[:8],
        likely_hooks=(context['likely_hooks'] + current_context['hooks'] + current_news['hooks'])[:8],
        context_notes=(context['context_notes'] + current_context['notes'] + current_news['notes'])[:8],
        opening_plan=live_plan['opening_plan'],
        post_opening_plan=live_plan['post_opening_plan'],
        qa_transition_plan=live_plan['qa_transition_plan'],
        strike_priority=strike_priority,
        pre_event_summary=dedupe(pre)[:8],
        live_trading_summary=dedupe(live)[:8],
        risk_summary=dedupe(risk)[:8],
        manual_trader_prompts=manual_trader_prompts,
        relevant_history_notes=relevant_history_notes,
        consensus_misread=consensus_misread,
        semantic_families=semantic_families,
        attention_allocation=attention_allocation,
        transcript_matches=transcript_matches,
    )
