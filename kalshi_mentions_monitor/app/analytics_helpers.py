from __future__ import annotations

from .analysis_models import StrikeAnalysis
from .models import Classification
from .ranking_sports import sports_bucket


def build_relevant_history_notes(classification: Classification | None, event_title: str, strike_analyses: list[StrikeAnalysis] | None = None) -> list[str]:
    if classification is None:
        return ['Историю без классификации события использовать осторожно: сначала уточни формат и спикера.']

    title = (event_title or '').lower()
    notes: list[str] = []
    labels = [x.label.lower() for x in (strike_analyses or [])]

    if classification.market_group == 'sports_announcer_mentions':
        notes.extend([
            'Не используй all-games sample подряд: полезнее same-broadcast, same-announcer crew и похожий game script.',
            'Prime-time и high-narrative games могут резко отличаться от обычной регулярки.',
        ])
        sports_buckets = [sports_bucket(x.label.lower()) for x in (strike_analyses or [])]
        if sports_buckets.count('narrative-tag') >= 4:
            notes.append('Если basket перегружен narrative tags, same-game history по shouty storylines полезнее общей сезонной частоты.')
        if sports_buckets.count('review-trigger') + sports_buckets.count('injury-contact') + sports_buckets.count('play-sequence') <= 5:
            notes.append('Когда live-structural cluster узкий, полезнее смотреть похожие игры с тем же announcer crew, а не broad sample.')
    elif classification.market_group == 'earnings_or_corporate_mentions':
        notes.extend([
            'Смотри не все earnings calls подряд, а same-company и по возможности same-quarter / same-setup samples.',
            'Отдельно разделяй prepared remarks history и analyst Q&A history.',
        ])
    elif classification.market_group in {'political_mentions', 'legal_court_mentions'}:
        notes.extend([
            'Не смешивай opening remarks, interview, hearing и press conference в один historical bucket.',
            'Recent-format samples обычно полезнее, чем дальняя история без учёта текущего режима спикера.',
        ])
    else:
        notes.append('Используй только максимально близкий comparison set по формату события; generic history здесь слабее помогает.')

    if classification.market_subtype == 'speech':
        notes.append('Для speech baskets полезнее смотреть похожие scripted openings, а не любые политические появления подряд.')
        if sum(1 for x in labels if any(t in x for t in ['history', 'historic', 'future', 'freedom', 'america', 'greatness'])) >= 2:
            notes.append('Если basket перегружен rhetorical tails, полезнее same-format scripted openings, а не broad political transcript history.')
    if classification.market_subtype == 'civic_announcement':
        notes.append('Для local/civic events полезнее same-office и same-city samples, чем generic national political history.')
        if sum(1 for x in labels if any(t in x for t in ['budget', 'housing', 'rent', 'tax', 'nypd', 'subway', 'school'])) >= 3:
            notes.append('Если local governance cluster широкий, история по same-city issues полезнее, чем national cable-news priors.')
    if classification.market_subtype == 'podcast_or_stream':
        notes.append('Для podcasts полезнее same-host chemistry и same-show format, чем generic long-form media appearances.')
        if sum(1 for x in labels if any(t in x for t in ['huberman', 'sleep', 'silicon valley', 'crypto', 'startup', 'supplement', 'longevity'])) >= 2:
            notes.append('Если basket держится на host-chemistry cluster, смотри похожие episodes/guests, а не generic topic frequency.')
    if 'prime minister' in title or 'house of commons' in title:
        notes.append('Для PMQ-подобных событий полезнее question-heavy samples, а не обычные prepared speeches.')
    if 'earnings call' in title:
        notes.append('Для earnings call baseline строится отдельно по prepared remarks и отдельно по Q&A.')
    return notes[:5]


def build_consensus_misread_notes(classification: Classification | None, event_title: str, strike_analyses: list[StrikeAnalysis]) -> list[str]:
    if classification is None:
        return ['Рынок может ошибаться просто из-за неверно распознанного формата события.']

    notes: list[str] = []
    title = (event_title or '').lower()
    strike_types = [x.rank.strike_type for x in strike_analyses]
    labels = [x.label.lower() for x in strike_analyses]

    baseline_count = sum(1 for x in strike_types if x == 'baseline speech')
    odd_count = sum(1 for x in strike_types if x == 'odd tail')
    rules_count = sum(1 for x in strike_types if x in {'special rule', 'nqe'})
    family_count = sum(1 for x in labels if any(t in x for t in ['children', 'family', 'school', 'youth', 'safe', 'privacy']))
    geo_count = sum(1 for x in labels if any(t in x for t in ['iran', 'israel', 'ukraine', 'peace', 'security']))
    name_count = sum(1 for x in labels if any(t in x for t in ['donald', 'barron', 'melania', 'ivanka', 'trump']))
    tech_count = sum(1 for x in labels if any(t in x for t in ['ai', 'chatgpt', 'tech', 'technology']))

    if classification.market_subtype == 'speech':
        notes.append('В speech basket рынок часто путает broad theme с exact token hit rate; правильная идея не равна правильному слову.')
        if baseline_count and odd_count:
            notes.append('Здесь особенно важно не ставить baseline words и odd tails в один bucket: opening basket и дальние хвосты должны прайситься по-разному.')
        if family_count >= 2:
            notes.append('Если название события тянет в family/social framing, crowd может механически завышать весь family cluster, хотя реальный opening может задеть только 1–2 базовых слова.')
        if geo_count >= 2:
            notes.append('Geo/conflict words здесь легко перепрайсить по headline association, хотя без явного topic pivot они могут вообще не ожить в opening.')
        if name_count >= 2:
            notes.append('Name strikes crowd часто тащит вслед за общим Trump-family narrative, хотя exact name exposure обычно уже намного уже, чем общий тематический фон.')
        if tech_count >= 1:
            notes.append('Tech tails типа AI/ChatGPT выглядят современно и headline-friendly, но без явного мостика из темы события это чаще false relevance, чем core basket.')
        rhetorical_count = sum(1 for x in labels if any(t in x for t in ['history', 'historic', 'future', 'freedom', 'america', 'greatness']))
        if rhetorical_count >= 2:
            notes.append('Rhetorical cluster легко выглядит “естественно для речи”, но crowd часто переоценивает style words как будто это concrete message path.')
    if classification.market_subtype == 'civic_announcement':
        notes.append('В local/civic events crowd часто overprojects national political narratives на более узкий office-framed event.')
        notes.append('Title relevance здесь легко перепутать с real speech path: headline city issue не значит, что exact token organically появится в office statement.')
        local_count = sum(1 for x in labels if any(t in x for t in ['budget', 'housing', 'rent', 'tax', 'nypd', 'subway', 'school']))
        national_count = sum(1 for x in labels if any(t in x for t in ['trump', 'israel', 'iran', 'ukraine', 'china', 'ai', 'chatgpt']))
        if local_count >= 3:
            notes.append('Local governance cluster должен читаться отдельно: city-policy words не стоит мешать с generic national talking points в один bucket.')
        if national_count >= 2:
            notes.append('Если в civic basket много national tails, crowd может перепутать headline politics с реальным office-framing path.')
    if classification.market_subtype == 'podcast_or_stream':
        notes.append('В podcasts crowd часто путает broad topic affinity гостей с реальным probability, что тема вообще зайдёт в live conversation.')
        notes.append('Long-form banter markets легко перепрайсить по clip-worthy narrative, хотя разговор может уйти совсем в другой lane.')
        chemistry_count = sum(1 for x in labels if any(t in x for t in ['huberman', 'sleep', 'silicon valley', 'crypto', 'startup', 'supplement', 'longevity']))
        forced_pivot_count = sum(1 for x in labels if any(t in x for t in ['election', 'ukraine', 'war', 'inflation', 'fed']))
        if chemistry_count >= 2:
            notes.append('Host-chemistry cluster обычно живёт лучше forced topical tails: знакомые shared obsessions crowd часто недооценивает.')
        if forced_pivot_count >= 2:
            notes.append('Forced topical cluster легко выглядит релевантно на бумаге, но без жёсткого pivot может вообще не появиться в разговоре.')
    if classification.market_group == 'sports_announcer_mentions':
        notes.append('В sports mentions crowd часто недооценивает, насколько сильно same announcer меняет hit rate при другом game script.')
        sports_buckets = [sports_bucket(x.label.lower()) for x in strike_analyses]
        if sports_buckets.count('broadcast-filler') >= 2:
            notes.append('Broadcast filler cluster легко становится overowned: arena/crowd/stadium words часто выглядят “естественно”, но переоцениваются толпой.')
        if sports_buckets.count('narrative-tag') >= 4:
            notes.append('Narrative-tag cluster может быть переполнен headline associations: MVP/Jordan/Playoff/Draft не равны live path сами по себе.')
        if sports_buckets.count('review-trigger') + sports_buckets.count('injury-contact') + sports_buckets.count('play-sequence') <= 5:
            notes.append('Если в basket мало реально live-structural words, эти немногие paths могут быть важнее, чем общий шум narrative cluster.')
    if classification.phase_profile in {'mixed', 'qa_heavy'}:
        notes.append('Рынок может слишком рано убивать yes после opening, хотя часть страйков живёт только в Q&A / follow-up phase.')
    if classification.market_group == 'sports_announcer_mentions':
        notes.append('Рынок может переоценивать общий historical hit rate без поправки на конкретный broadcast flow и game state.')
    if classification.market_group == 'earnings_or_corporate_mentions':
        notes.append('Рынок может смешивать prepared-remarks words и analyst-Q&A words в один bucket.')
    if 'stretch cluster' in strike_types:
        notes.append('Stretch words часто переплачены просто за thematic adjacency к core basket, а не за свой собственный hit path.')
    if rules_count:
        notes.append('Rules-sensitive strikes нельзя прайсить как обычные basket words: range / wording caveats здесь сами по себе часть риска.')
    if 'closed press' in title or 'signing' in title:
        notes.append('Рынок может переоценивать closed/open press headline и недооценивать фактическую длину и looseness события.')
    return notes[:6]


def infer_phase_fit(classification: Classification | None, strike: StrikeAnalysis) -> str:
    stype = strike.rank.strike_type.lower()

    if stype == 'nqe':
        return 'service-only'
    if stype == 'qa-sensitive':
        return 'q&a-heavy'
    if stype in {'game-state', 'broadcast-flow'}:
        return 'game-state-sensitive'
    if classification is None:
        return 'unknown'
    if classification.market_subtype == 'speech' and classification.phase_profile == 'opening_heavy':
        if stype == 'baseline speech':
            return 'opening-heavy'
        if stype == 'stretch cluster':
            return 'opening-if-theme-expands'
        if stype == 'odd tail':
            return 'only-alive-if-topic-breaks'
        if stype == 'theme-linked':
            return 'opening-or-transition'
    if classification.market_group == 'earnings_or_corporate_mentions':
        if stype == 'theme-linked':
            return 'prepared-or-q&a-dependent'
        return 'q&a-watch'
    if classification.market_group == 'legal_court_mentions':
        return 'question-chain-sensitive' if stype != 'special rule' else 'speaker-identity-and-rules-sensitive'
    return 'mixed'


def build_semantic_families(classification: Classification | None, strike_analyses: list[StrikeAnalysis]) -> list[dict]:
    if classification is None or classification.market_subtype != 'speech':
        return []

    families = {
        'baseline-family-safety': [],
        'baseline-leadership-future': [],
        'stretch-economy-work': [],
        'stretch-geopolitics-security': [],
        'odd-tail': [],
    }
    for strike in strike_analyses:
        label = strike.label.lower()
        if any(x in label for x in ['child', 'family', 'school', 'safe', 'privacy', 'security']):
            families['baseline-family-safety'].append(strike.label)
        elif any(x in label for x in ['lead', 'leader', 'leadership', 'future', 'history', 'historic']):
            families['baseline-leadership-future'].append(strike.label)
        elif any(x in label for x in ['econom', 'job', 'afford', 'inflation', 'growth']):
            families['stretch-economy-work'].append(strike.label)
        elif any(x in label for x in ['peace', 'war', 'iran', 'ukraine', 'israel', 'security']):
            families['stretch-geopolitics-security'].append(strike.label)
        elif strike.rank.strike_type in {'odd tail', 'nqe'}:
            families['odd-tail'].append(strike.label)

    out = []
    for family, labels in families.items():
        if labels:
            out.append({'family': family, 'labels': labels[:8]})
    return out[:5]
