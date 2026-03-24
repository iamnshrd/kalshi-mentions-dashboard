from __future__ import annotations

from .models import Classification


def build_context_enrichment(event_title: str, classification: Classification) -> dict:
    title = (event_title or '').lower()
    notes: list[str] = []
    checks: list[str] = []
    likely_hooks: list[str] = []

    if classification.market_group == 'political_mentions':
        checks.extend([
            'Проверь новости за 48–72 часа по стране / штату / площадке события.',
            'Отдельно смотри violence / immigration / Israel / economy hooks в локальной повестке.',
            'Проверь, кто ещё участвует в событии и есть ли риск перехода в Q&A / press scrum.',
        ])
        likely_hooks.extend(['local incident', 'policy headline', 'question-driven narrative shift'])
        notes.append('Для political mentions current events часто важнее последних transcript counts.')

    elif classification.market_group == 'legal_court_mentions':
        checks.extend([
            'Проверь, кто именно участвует: justice, witness, counsel, committee members.',
            'Прочитай rules буквально: кто должен сказать phrase, чтобы strike засчитался.',
            'Уточни, это formal hearing / oral arguments / testimony или remarks-style event.',
        ])
        likely_hooks.extend(['speaker identity', 'question chain', 'case-specific terminology'])
        notes.append('В legal/court markets wording и identity speaker risk почти всегда выше среднего.')

    elif classification.market_group == 'earnings_or_corporate_mentions':
        checks.extend([
            'Проверь последний earnings transcript и investor materials.',
            'Отметь темы, которые likely script-driven, и темы, которые скорее всплывут только в analyst Q&A.',
            'Смотри свежие company-specific catalysts: downgrade, product issue, layoffs, guidance pressure.',
        ])
        likely_hooks.extend(['scripted guidance', 'analyst follow-up', 'current quarter issue'])
        notes.append('Для earnings history полезна, но без quarter-specific context легко даёт ложную уверенность.')

    elif classification.market_group == 'sports_announcer_mentions':
        checks.extend([
            'Проверь sport, matchup, announcer crew и network/broadcast quirks.',
            'Смотри, есть ли pregame narrative, rivalry angle, injury storyline или weather/game-script factors.',
            'Заранее раздели strikes на baseline-driven и game-state-driven.',
        ])
        likely_hooks.extend(['replay sequence', 'close game script', 'blowout yap risk'])
        notes.append('В sports mentions game script и broadcast flow часто важнее общей сезонной частоты.')

    elif classification.market_group == 'culture_entertainment_mentions':
        checks.extend([
            'Проверь run-of-show, performer order, host duties и вероятные cameo/appearance hooks.',
            'Отдельно смотри social narrative и front-page retail flow risk.',
            'Проверь wording/rules для appearance, brand mention и identity-sensitive strikes.',
        ])
        likely_hooks.extend(['segment transition', 'surprise cameo', 'retail narrative blowoff'])
        notes.append('В culture/entertainment markets часто важнее flow и structure of show, чем история.')

    if 'prime minister' in title or 'house of commons' in title:
        notes.append('Parliament-style format часто ближе к adversarial Q&A, чем к чистой prepared speech логике.')
    if 'earnings call' in title:
        notes.append('Assume mixed format by default: prepared remarks first, analyst Q&A second.')
    if 'announcers' in title:
        notes.append('Live repricing после ключевых игровых моментов обычно важнее prematch static view.')

    return {
        'context_checks': checks,
        'likely_hooks': likely_hooks,
        'context_notes': notes,
    }
