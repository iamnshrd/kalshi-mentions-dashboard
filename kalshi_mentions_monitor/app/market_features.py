from __future__ import annotations

import re

from .models import NormalizedMarket


def market_text(market: NormalizedMarket) -> str:
    return ' '.join(
        str(x or '')
        for x in [
            market.title,
            market.subtitle,
            market.yes_sub_title,
            market.no_sub_title,
            market.rules_primary,
            market.rules_secondary,
            market.event_ticker,
            market.series_ticker,
            market.market_type,
        ]
    ).lower()


def infer_sport(text: str) -> str | None:
    mapping = {
        'mlb': 'mlb',
        'baseball': 'mlb',
        'nfl': 'nfl',
        'football': 'nfl',
        'nba': 'nba',
        'basketball': 'nba',
        'nhl': 'nhl',
        'hockey': 'nhl',
        'soccer': 'soccer',
        'premier league': 'soccer',
        'march madness': 'college_basketball',
        'ncaa': 'college_sports',
    }
    for k, v in mapping.items():
        if k in text:
            return v
    return None


def infer_event_format(text: str) -> str:
    if 'earnings call' in text:
        return 'earnings_call'
    if 'press conference' in text or 'press briefing' in text:
        return 'press_conference'
    if 'interview' in text:
        return 'interview'
    if 'rally' in text:
        return 'rally'
    if 'oral arguments' in text or 'hearing' in text:
        return 'hearing'
    if 'remarks' in text or 'speech' in text:
        return 'speech'
    if 'during the game' in text or 'announcers say' in text:
        return 'game_broadcast'
    return 'unknown'


def extract_speaker(title: str) -> str | None:
    if not title:
        return None
    patterns = [
        r'what will (.+?) say during',
        r'what will (.+?) mention during',
        r'what will the announcers say during',
    ]
    t = title.lower()
    for p in patterns:
        m = re.search(p, t)
        if m:
            val = m.group(1).strip()
            if val == 'the announcers':
                return 'announcers'
            return val
    return None
