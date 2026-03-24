from __future__ import annotations

from .models import Classification


def build_live_plan(classification: Classification) -> dict:
    opening: list[str] = []
    post_opening: list[str] = []
    qa_transition: list[str] = []

    if classification.market_group == 'political_mentions':
        opening = [
            'Определи dominant topic cluster в первые минуты, а не следи за одним isolated strike.',
            'Смотри, подтверждает ли opening базовый expected theme или ломает его через current event pivot.',
        ]
        post_opening = [
            'Если opening прошёл без hit, не держи NO автоматически: сначала реши, был ли strike opening-heavy или Q&A-heavy.',
            'Переоцени narrative buckets целиком, а не отдельные слова.',
        ]
        qa_transition = [
            'При переходе в Q&A поднимай вес question-driven strikes.',
            'Если журналисты или оппоненты тащат новую тему, перепрайсь whole related cluster immediately.',
        ]
        if classification.market_subtype == 'civic_announcement':
            opening = [
                'Сначала проверь, держится ли спикер в узком office/agency framing или уходит в broader politics.',
                'Не тащи national narrative в локальное event framing без явного сигнала в opening.',
            ]
            post_opening = [
                'Если opening остался формальным и office-heavy, режь tails, которым нужен wider political rant path.',
                'Если local governance topic неожиданно раскрывается широко, перепрайсь тематические кластеры, а не одно слово.',
            ]
            qa_transition = [
                'Если событие уходит в press scrum, вес question-driven strikes резко растёт.',
                'Local press questions могут быстро сменить office framing на conflict/policy lane.',
            ]

    elif classification.market_group == 'legal_court_mentions':
        opening = [
            'Сначала убедись, кто именно говорит и кто вообще может зарезолвить strike.',
            'Не путай procedural language с meaningful strike context.',
        ]
        post_opening = [
            'После старта hearing/oral arguments сильнее отслеживай chains of questioning, а не isolated remarks.',
            'Если event оказался более adversarial, повышай вес Q&A-sensitive/legal-context strikes.',
        ]
        qa_transition = [
            'На question-heavy flow внимательно следи за speaker identity и wording precision.',
            'Не overreact на partial phrase, если rules чувствительны к точной формулировке.',
        ]

    elif classification.market_group == 'earnings_or_corporate_mentions':
        opening = [
            'В prepared remarks ищи management-script phrases и baseline guidance language.',
            'Не делай вывод, что unsaid strike dead, пока не понял, живёт ли он в analyst Q&A.',
        ]
        post_opening = [
            'Сразу после prepared remarks пересчитай Q&A-only fair values для analyst-driven strikes.',
            'Если call unusually short, режь Q&A-sensitive tails сильнее.',
        ]
        qa_transition = [
            'Во время analyst Q&A повышай вес current-quarter issue strikes и follow-up dependent language.',
            'Если вопросы мягкие, не overpay за Q&A-sensitive yeses.',
        ]

    elif classification.market_group == 'sports_announcer_mentions':
        opening = [
            'Не фиксируйся на prematch baseline: live game state быстро меняет relevance strikes.',
            'Следи за announcer flow, network style и early narrative framing.',
        ]
        post_opening = [
            'После ключевых игровых моментов repricing должен идти по clusters: replay, penalty, measurement, blowout yapping.',
            'Если game script ломает prematch assumption, пересобирай view быстро и без якорения.',
        ]
        qa_transition = [
            'Q&A transition not applicable in classic sports broadcast; вместо этого думай segment transitions: live play, replay, break, postgame.',
        ]

    elif classification.market_subtype == 'podcast_or_stream':
        opening = [
            'Не переоцени intro banter: сначала пойми, какой conversational lane реально закрепился.',
            'Смотри, есть ли у co-hosts/guest естественный bridge к нужным topic clusters.',
        ]
        post_opening = [
            'Если разговор закрепился в одном lane, режь страйки, которым нужен жёсткий topic pivot.',
            'На podcasts важнее flow and chemistry, чем scripted-opening analogies.',
        ]
        qa_transition = [
            'Классического Q&A может не быть; вместо этого следи за guest pivot, tangent и reaction loops.',
        ]
    else:
        opening = ['Сначала пойми реальный формат события, потом уже aggressively repricing strikes.']
        post_opening = ['После первой фазы события пересчитай, какие strikes ещё реально живы.']
        qa_transition = ['Если event перешёл в questions/interaction, повысь вес question-driven strikes.']

    return {
        'opening_plan': opening,
        'post_opening_plan': post_opening,
        'qa_transition_plan': qa_transition,
    }
