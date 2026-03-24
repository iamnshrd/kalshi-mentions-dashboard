from __future__ import annotations

from .models import Classification, NormalizedMarket, Recommendation


def build_recommendation(market: NormalizedMarket, c: Classification) -> Recommendation:
    pre: list[str] = []
    live: list[str] = []
    risk: list[str] = []
    priority = "normal"

    if c.market_group == "political_mentions":
        pre.extend([
            "Проверь local/state news за последние 48–72 часа; recent incidents часто важнее сырой истории.",
            "Не опирайся только на последние speeches/transcript counts; разбей strikes на structural, contextual и Q&A-dependent.",
            "Сгруппируй тематически связанные strikes в narrative buckets, чтобы не дублировать один и тот же риск несколько раз.",
        ])
        live.extend([
            "В первые минуты определи dominant theme cluster, а не только отдельные слова.",
            "Если спикер подхватывает локальную или свежую новость, перепрайсь весь связанный bucket сразу.",
            "После opening не держи NO механически: если strike жил в Q&A, рыночная компрессия NO может быть чрезмерной.",
        ])
        risk.extend([
            "Высокая чувствительность к current events.",
            "Связанные страйки могут быть фактически одной ставкой на один narrative.",
            "Исторические паттерны легко переобучаются без учёта контекста.",
        ])
        priority = "high"

    elif c.market_group == "earnings_or_corporate_mentions":
        pre.extend([
            "Посмотри 4–8 релевантных прошлых calls и раздели recurring phrases между prepared remarks и analyst Q&A.",
            "Не используй сырые transcript frequencies без сегментации по quarter и типу события.",
            "Выдели management-script words против analyst-driven words до старта события.",
        ])
        live.extend([
            "После prepared remarks полностью перепрайсь Q&A-heavy strikes.",
            "Отсутствие слова в script не убивает Q&A-dependent strike автоматически.",
            "Следи за длиной Q&A и за тем, насколько аналитики давят на чувствительные темы.",
        ])
        risk.extend([
            "Средняя зависимость от контекста, но высокая чувствительность к сегментации prepared vs Q&A.",
            "Ошибки часто возникают от грубого использования истории без event-specific поправок.",
        ])

    elif c.market_group == "sports_announcer_mentions":
        pre.extend([
            "Проверь announcer history, network/broadcast quirks и game-type baseline.",
            "Раздели strikes на structural, replay-driven, game-state-driven и incidental chaos strikes.",
            "Избегай слабомоделируемых мусорных strikes, если у тебя нет отдельного edge по ним.",
        ])
        live.extend([
            "Перепрайсь по game state: blowout повышает incidental yap risk, close game повышает structural relevance.",
            "Replay/penalty/measurement sequences часто важнее сырой общей частоты по сезону.",
            "После ключевых игровых эпизодов пересматривай не один strike, а весь тематически связанный cluster.",
        ])
        risk.extend([
            "Сильная зависимость от game script.",
            "Broadcast/network quirks могут заметно смещать fair value.",
            "Связанные strikes часто коррелируют сильнее, чем кажется до игры.",
        ])
        priority = "high"

    elif c.market_group == "culture_entertainment_mentions":
        pre.extend([
            "Проверь structure of show: segments, host duties, performer slots, likely cameos.",
            "Ожидай dumb flow на front-page массовых событиях и заранее выдели narrative-driven traps.",
            "Отдельно проверь wording/rules, если рынок завязан на appearance, brand mention или specific identity conditions.",
        ])
        live.extend([
            "Реагируй на segment transitions, а не только на сами слова: рынок часто overreacts к первым визуальным/сюжетным сигналам.",
            "Если это one-off show, уменьшай уверенность в сырых historical comparisons.",
            "На массовом event flow цена может ломаться из-за retail narrative, а не из-за реального fair value.",
        ])
        risk.extend([
            "Высокий front-page / retail flow risk.",
            "One-off format risk: мало повторяемой истории.",
        ])
        priority = "high"

    else:
        pre.extend([
            "Классификация неуверенная: сначала прочитай rules и resolution text буквально.",
            "Сделай короткий manual review before trading; не опирайся на автоматическую рекомендацию как на истину.",
        ])
        live.extend([
            "Торгуй только после ручной валидации формата и ключевых traps.",
            "Если рынок выглядит one-off и неочевидным, снижать размер или пропускать — нормальное решение.",
        ])
        risk.extend([
            "Неуверенная классификация.",
            "Повышенный риск неправильной автоматической группировки.",
        ])
        priority = "low"

    if c.phase_profile in {"qa_heavy", "mixed"}:
        pre.append("Заранее раздели strikes на opening-heavy и Q&A-heavy, чтобы не принимать решения по памяти в лайве.")
        live.append("После opening обязательно пересчитай fair values для Q&A-only сценария.")
    if c.context_sensitivity == "high":
        pre.append("Current events обязательны к просмотру до события; исторический baseline сам по себе недостаточен.")
    if c.rules_risk in {"medium", "high"}:
        risk.append("Повышенный rules risk: уменьшай размер и не называй рынок bond-подобным без ручной проверки.")
        priority = "normal" if priority == "high" else priority

    return Recommendation(
        market_id=market.market_id,
        pre_event_recommendations=pre,
        live_trading_recommendations=live,
        risk_notes=risk,
        priority_level=priority,
    )
