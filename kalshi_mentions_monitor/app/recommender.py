from __future__ import annotations

from .models import Classification, NormalizedMarket, Recommendation


def build_recommendation(market: NormalizedMarket, c: Classification) -> Recommendation:
    pre: list[str] = []
    live: list[str] = []
    risk: list[str] = []
    priority = 'normal'

    if c.market_group == 'political_mentions':
        pre.extend([
            'Проверь local/state news за последние 48–72 часа; свежие инциденты часто ломают исторический baseline.',
            'Не опирайся только на последние speeches/transcript counts; раздели strikes на structural, contextual и Q&A-dependent.',
            'Сгруппируй тематически связанные strikes в narrative buckets, чтобы не задублировать один и тот же риск.',
        ])
        live.extend([
            'В первые минуты определи dominant theme cluster, а не отдельное слово.',
            'Если спикер подхватывает локальную новость, перепрайсь весь связанный bucket сразу.',
            'После opening не держи NO механически: если strike жил в Q&A, компрессия рынка может быть чрезмерной.',
        ])
        risk.extend([
            'Высокая чувствительность к current events.',
            'Связанные страйки могут быть по сути одной ставкой на один narrative.',
            'Исторические паттерны легко переобучаются без учёта контекста.',
        ])
        priority = 'high'

    elif c.market_group == 'legal_court_mentions':
        pre.extend([
            'Сначала пойми формат: oral arguments, hearing, prepared remarks или Q&A-like exchange.',
            'Проверь, кто именно должен сказать слово и как rules трактуют judge/justice/lawyer mentions.',
            'Раздели strikes на legal-core, question-driven и current-case-context-dependent.',
        ])
        live.extend([
            'Следи за тем, кто говорит: судья, адвокат, представитель стороны — это может быть критично для резолва.',
            'Если формат похож на hearing/oral arguments, Q&A-heavy repricing обязательна.',
            'Не путай чисто юридический контекст со случайным употреблением слова; exact wording matters more than vibes.',
        ])
        risk.extend([
            'Высокий риск ошибиться в том, кто именно должен произнести phrase.',
            'Legal context может увеличивать side-door hit risk для seemingly narrow strikes.',
        ])
        priority = 'high'

    elif c.market_group == 'earnings_or_corporate_mentions':
        pre.extend([
            'Посмотри 4–8 релевантных прошлых calls и раздели recurring phrases между prepared remarks и analyst Q&A.',
            'Не используй сырые transcript frequencies без сегментации по quarter и типу события.',
            'Выдели management-script words против analyst-driven words до старта события.',
        ])
        live.extend([
            'После prepared remarks полностью перепрайсь Q&A-heavy strikes.',
            'Отсутствие слова в script не убивает Q&A-dependent strike автоматически.',
            'Следи за длиной Q&A и тем, насколько аналитики давят на чувствительные темы.',
        ])
        risk.extend([
            'Средняя зависимость от контекста, но высокая чувствительность к сегментации prepared vs Q&A.',
            'Ошибки часто идут от грубого использования истории без event-specific поправок.',
        ])

    elif c.market_group == 'sports_announcer_mentions':
        pre.extend([
            'Проверь announcer history, sport/network quirks и game-type baseline.',
            'Раздели strikes на structural, replay-driven, game-state-driven и incidental chaos strikes.',
            'Не трогай слабомоделируемые мусорные strikes без отдельного edge.',
        ])
        live.extend([
            'Перепрайсь по game state: blowout повышает incidental yap risk, close game повышает structural relevance.',
            'Replay/penalty/measurement sequences важнее общей частоты по сезону.',
            'После ключевых игровых эпизодов пересматривай не один strike, а тематически связанный cluster.',
        ])
        risk.extend([
            'Сильная зависимость от game script.',
            'Broadcast/network quirks могут смещать fair value сильнее, чем кажется.',
            'Связанные strikes часто коррелируют сильнее, чем видно до игры.',
        ])
        priority = 'high'

    elif c.market_group == 'culture_entertainment_mentions':
        pre.extend([
            'Проверь structure of show: segments, host duties, performer slots, likely cameos.',
            'Ожидай dumb flow на front-page массовых событиях и заранее выдели narrative-driven traps.',
            'Отдельно проверь wording/rules, если рынок завязан на appearance, brand mention или specific identity conditions.',
        ])
        live.extend([
            'Реагируй на segment transitions, а не только на сами слова.',
            'Если это one-off show, уменьшай уверенность в сырых historical comparisons.',
            'На массовом event flow цена часто ломается из-за retail narrative, а не из-за fair value.',
        ])
        risk.extend([
            'Высокий front-page / retail flow risk.',
            'One-off format risk: мало повторяемой истории.',
        ])
        priority = 'high'

    else:
        pre.extend([
            'Классификация неуверенная: сначала прочитай rules и resolution text буквально.',
            'Сделай короткий manual review before trading; не используй автоматическую рекомендацию как источник истины.',
        ])
        live.extend([
            'Торгуй только после ручной валидации формата и ключевых traps.',
            'Если рынок выглядит one-off и неочевидным, снижать размер или пропускать — нормальное решение.',
        ])
        risk.extend([
            'Неуверенная классификация.',
            'Повышенный риск неправильной автоматической группировки.',
        ])
        priority = 'low'

    if c.phase_profile in {'qa_heavy', 'mixed'}:
        pre.append('Заранее раздели strikes на opening-heavy и Q&A-heavy, чтобы не держать всё в голове в лайве.')
        live.append('После opening обязательно пересчитай fair values для Q&A-only сценария.')
    if c.context_sensitivity == 'high':
        pre.append('Current events обязательны к просмотру до события; исторический baseline сам по себе недостаточен.')
    if c.rules_risk in {'medium', 'high'}:
        risk.append('Повышенный rules risk: уменьшай размер и не считай рынок bond-подобным без ручной проверки.')
        priority = 'normal' if priority == 'high' else priority

    return Recommendation(
        market_id=market.market_id,
        pre_event_recommendations=pre,
        live_trading_recommendations=live,
        risk_notes=risk,
        priority_level=priority,
    )
