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
    low = (text or '').lower()

    priority_patterns = [
        ('professional basketball game', 'nba'),
        ('basketball game', 'nba'),
        ('nba', 'nba'),
        ('professional football game', 'nfl'),
        ('football game', 'nfl'),
        ('nfl', 'nfl'),
        ('professional baseball game', 'mlb'),
        ('baseball game', 'mlb'),
        ('mlb', 'mlb'),
        ('professional hockey game', 'nhl'),
        ('hockey game', 'nhl'),
        ('nhl', 'nhl'),
        ('soccer match', 'soccer'),
        ('premier league', 'soccer'),
        ('soccer', 'soccer'),
        ('march madness', 'college_basketball'),
        ('ncaa basketball', 'college_basketball'),
        ('ncaa football', 'college_football'),
        ('ncaa', 'college_sports'),
    ]
    for pat, sport in priority_patterns:
        if pat in low:
            return sport

    fallback_patterns = [
        ('basketball', 'nba'),
        ('football', 'nfl'),
        ('baseball', 'mlb'),
        ('hockey', 'nhl'),
    ]
    for pat, sport in fallback_patterns:
        if pat in low:
            return sport
    return None


def infer_event_format(text: str) -> str:
    if 'earnings call' in text:
        return 'earnings_call'
    if 'press conference' in text or 'press briefing' in text:
        return 'press_conference'
    if 'podcast' in text:
        return 'podcast'
    if 'interview' in text:
        return 'interview'
    if 'rally' in text:
        return 'rally'
    if 'oral arguments' in text or 'hearing' in text:
        return 'hearing'
    if 'announcement' in text or 'remarks' in text or 'speech' in text:
        return 'speech'
    if 'during the game' in text or 'announcers say' in text or 'the announcers' in text:
        return 'game_broadcast'
    return 'unknown'


def extract_speaker(title: str) -> str | None:
    if not title:
        return None
    t = title.lower()
    if 'what will the announcers say during' in t:
        return 'announcers'

    patterns = [
        r'what will (.+?) say during',
        r'what will (.+?) mention during',
    ]
    for p in patterns:
        m = re.search(p, t)
        if m:
            return m.group(1).strip()
    return None
