from __future__ import annotations

from .analysis_models import StrikeAnalysis
from .models import Classification


def build_current_context_signals(event_title: str, classification: Classification | None, strike_analyses: list[StrikeAnalysis]) -> dict:
    if classification is None:
        return {'signals': [], 'hooks': [], 'notes': []}

    title = (event_title or '').lower()
    labels = [x.label.lower() for x in strike_analyses]
    signals: list[str] = []
    hooks: list[str] = []
    notes: list[str] = []

    family_count = sum(1 for x in labels if any(t in x for t in ['children', 'family', 'school', 'youth', 'privacy', 'safe']))
    geo_count = sum(1 for x in labels if any(t in x for t in ['iran', 'israel', 'ukraine', 'peace', 'security']))
    local_count = sum(1 for x in labels if any(t in x for t in ['budget', 'housing', 'rent', 'tax', 'nypd', 'subway', 'school']))
    chemistry_count = sum(1 for x in labels if any(t in x for t in ['huberman', 'sleep', 'silicon valley', 'crypto', 'startup', 'supplement', 'longevity']))
    review_count = sum(1 for x in labels if any(t in x for t in ['tech', 'technical', 'review', 'challenge', 'flag']))
    filler_count = sum(1 for x in labels if any(t in x for t in ['crowd', 'american airlines']))

    if classification.market_subtype == 'civic_announcement':
        signals.extend([
            'Проверь, какой именно официальный повод у события сегодня: policy rollout, staffing signal, local incident response или ceremonial appearance.',
            'Сопоставь basket со свежим local news cycle, а не с national cable framing.',
        ])
        hooks.extend(['office framing', 'local governance hook', 'press scrum risk'])
        if local_count >= 3:
            notes.append('Текущий basket уже намекает на city-policy framing; local issue pressure здесь важнее generic national politics.')
        if geo_count >= 2:
            notes.append('Geo/national tails стоит оживлять только если local event реально уходит из office framing в broader politics.')

    if classification.market_subtype == 'speech':
        signals.extend([
            'Сначала проверь, какой narrative cluster уже живёт в новостях вокруг этого спикера именно сегодня.',
            'Отдели headline frame события от того, что реально естественно для scripted opening.',
        ])
        hooks.extend(['opening frame', 'headline-topic pressure'])
        if family_count >= 2:
            notes.append('Family/social cluster сейчас выглядит как headline-sensitive; важно проверить, это реальная текущая повестка или просто framing названия события.')
        if geo_count >= 2:
            notes.append('Geo cluster имеет смысл только если у события есть свежий forced news hook; без него это чаще paper relevance.')

    if classification.market_subtype == 'podcast_or_stream':
        signals.extend([
            'Проверь, что именно сейчас двигает conversation incentives у host/guest: свежий clip cycle, Twitter beef, product/news hook или recurring obsession.',
            'Не путай topic affinity с actual live entry point в разговор.',
        ])
        hooks.extend(['host chemistry', 'fresh clip cycle', 'guest pivot'])
        if chemistry_count >= 2:
            notes.append('Host-chemistry cluster уже выглядит центральным; current context здесь скорее в social/media loop, чем в formal news cycle.')
        if geo_count >= 2:
            notes.append('Hard-news tails без свежего media trigger обычно слабее, чем кажется на бумаге.')

    if classification.market_group == 'sports_announcer_mentions':
        signals.extend([
            'Проверь prematch storylines именно сегодняшней игры: injury report, seeding/playoff angle, revenge spot, broadcast narrative.',
            'Оцени, какие paths сегодня реально live: whistle/review, contact/injury, pace/shot-profile, crowd/arena noise.',
        ])
        hooks.extend(['injury report', 'seeding narrative', 'broadcast storyline'])
        if review_count >= 2:
            notes.append('Review/whistle cluster уже выглядит живым; current context должен подтвердить, есть ли matchup/ref narrative под это.')
        if filler_count >= 2:
            notes.append('Broadcast filler cluster стоит оживлять только если есть конкретный arena/broadcast story today, иначе это просто generic overowning.')

    if 'mayor' in title or "mayor's office" in title:
        notes.append('Mayor/office events часто живут вокруг very current city issue of the day, а не around broad ideological basket.')
    if 'podcast' in title:
        notes.append('Podcast current context часто приходит не из headline news, а из social/media loop последних 24–48 часов.')
    if 'announcers' in title:
        notes.append('Для announcer markets “current context” = matchup script + crew tendencies + broadcast setting, а не general sports news.')

    return {'signals': signals[:5], 'hooks': hooks[:5], 'notes': notes[:5]}
