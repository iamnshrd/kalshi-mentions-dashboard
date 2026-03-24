from __future__ import annotations

import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

from .models import Classification


SPORTS_TITLE_RE = re.compile(r'what will the announcers say during (.+?)\?$', re.IGNORECASE)
MATCHUP_RE = re.compile(r'(.+?)\s+vs\s+(.+?)\s+professional\s+(basketball|football|baseball|hockey)\s+game', re.IGNORECASE)

GOOD_SOURCE_HINTS = {
    'nytimes': 3,
    'the new york times': 3,
    'nyt': 3,
    'nbc new york': 3,
    'nyc.gov': 4,
    'nba': 4,
    'espn': 4,
    'sports illustrated': 2,
    'ap news': 3,
    'associated press': 3,
    'reuters': 3,
    'bloomberg': 3,
    'wsj': 3,
    'cbssports': 2,
    'the athletic': 3,
    'fox sports': 2,
}
BAD_SOURCE_HINTS = {
    'times of india': -4,
    'hindustan times': -2,
    'sling tv': -4,
    'how to watch': -4,
    'watch live': -3,
    'tv channel': -3,
    'live stream': -3,
    'yahoo': -1,
    'aol': -1,
}


@dataclass(slots=True)
class NewsHit:
    title: str
    link: str
    pub_date: str
    score: int = 0


def _clean(text: str) -> str:
    text = html.unescape(text or '')
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _extract_matchup_query(event_title: str) -> str:
    t = (event_title or '').strip()
    m = MATCHUP_RE.search(t)
    if not m:
        m2 = SPORTS_TITLE_RE.search(t)
        if not m2:
            return t
        t = m2.group(1)
        m = MATCHUP_RE.search(t)
        if not m:
            return t
    team1, team2, sport = [x.strip() for x in m.groups()]
    sport_term = {
        'basketball': 'NBA',
        'football': 'NFL',
        'baseball': 'MLB',
        'hockey': 'NHL',
    }.get(sport.lower(), sport)
    return f'{team1} {team2} {sport_term} preview injury report matchup'


def _build_query(event_title: str, classification: Classification | None) -> str:
    if classification and classification.market_group == 'sports_announcer_mentions':
        return _extract_matchup_query(event_title)

    parts = []
    if classification and classification.speaker and classification.speaker != 'unknown':
        parts.append(classification.speaker)
    if event_title:
        parts.append(event_title)
    if classification:
        if classification.market_subtype == 'civic_announcement':
            parts.append('city hall mayor office local policy')
        elif classification.market_subtype == 'podcast_or_stream':
            parts.append('podcast episode clip guest latest')
        elif classification.market_group == 'political_mentions':
            parts.append('latest remarks speech news')
    return ' '.join(parts[:4]).strip()


def _is_relevant_hit(title: str, event_title: str, classification: Classification | None) -> bool:
    low = title.lower()
    if classification and classification.market_group == 'sports_announcer_mentions':
        m = MATCHUP_RE.search(event_title or '')
        if m:
            team1, team2, sport = [x.strip().lower() for x in m.groups()]
            team1_key = team1.split()[0]
            team2_key = team2.split()[0]
            return (team1_key in low or team1 in low) and (team2_key in low or team2 in low)
    if classification and classification.market_subtype == 'civic_announcement' and classification.speaker and classification.speaker != 'unknown':
        return classification.speaker.split()[0].lower() in low
    return True


def _source_label(title: str) -> str:
    if ' - ' in title:
        return title.rsplit(' - ', 1)[-1].strip().lower()
    return ''


def _score_hit(title: str, link: str, classification: Classification | None) -> int:
    low = title.lower()
    src = _source_label(title)
    domain = urlparse(link).netloc.lower()
    score = 0

    for hint, val in GOOD_SOURCE_HINTS.items():
        if hint in src or hint in domain:
            score += val
    for hint, val in BAD_SOURCE_HINTS.items():
        if hint in src or hint in low or hint in domain:
            score += val

    if classification and classification.market_group == 'sports_announcer_mentions':
        if any(x in src for x in ['nba', 'espn', 'sports illustrated', 'cbs sports', 'the athletic']) or any(x in domain for x in ['nba.com', 'espn.com', 'si.com', 'cbssports.com', 'theathletic.com']):
            score += 3
        if any(x in low for x in ['injury report', 'preview', 'starting lineup', 'starting five', 'matchup']):
            score += 2
        if any(x in low for x in ['how to watch', 'tv channel', 'live stream']):
            score -= 4
    if classification and classification.market_subtype == 'civic_announcement':
        if 'gov' in domain or 'city' in src or 'nbc new york' in src or 'new york times' in src:
            score += 2
    return score


def fetch_current_news(event_title: str, classification: Classification | None, limit: int = 3) -> list[NewsHit]:
    query = _build_query(event_title, classification)
    if not query:
        return []
    url = 'https://news.google.com/rss/search?q=' + urllib.parse.quote(query)
    try:
        resp = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
    except Exception:
        return []

    out: list[NewsHit] = []
    fallback: list[NewsHit] = []
    for item in root.findall('.//item'):
        title = _clean(item.findtext('title') or '')
        link = _clean(item.findtext('link') or '')
        pub_date = _clean(item.findtext('pubDate') or '')
        if not title:
            continue
        if not _is_relevant_hit(title, event_title, classification):
            continue
        score = _score_hit(title, link, classification)
        hit = NewsHit(title=title, link=link, pub_date=pub_date, score=score)
        if score >= 0:
            out.append(hit)
        else:
            fallback.append(hit)
    out.sort(key=lambda x: (-x.score, x.title))
    if out:
        return out[:limit]
    fallback.sort(key=lambda x: (-x.score, x.title))
    if classification and classification.market_group == 'sports_announcer_mentions':
        fallback = [x for x in fallback if x.score >= -2]
    return fallback[:limit]


def build_news_context_notes(event_title: str, classification: Classification | None) -> dict:
    hits = fetch_current_news(event_title, classification, limit=3)
    if not hits:
        return {'checks': [], 'hooks': [], 'notes': []}

    min_score = 1
    if classification and classification.market_group == 'sports_announcer_mentions':
        min_score = 1  # sports headlines must clear quality bar; otherwise prefer no headline
    filtered = [h for h in hits if h.score >= min_score]
    if not filtered:
        return {'checks': [], 'hooks': [], 'notes': []}

    checks = ['Проверь свежие headlines по событию/спикеру: рынок может уже торговать вчерашний narrative.']
    hooks = ['fresh headline pressure']
    notes = []
    for hit in filtered[:3]:
        notes.append(f"Свежий headline: {hit.title}")
    if classification and classification.market_subtype == 'civic_announcement':
        hooks.append('today local issue')
    if classification and classification.market_subtype == 'podcast_or_stream':
        hooks.append('fresh media loop')
    if classification and classification.market_group == 'sports_announcer_mentions':
        hooks.append('prematch storyline today')
    return {'checks': checks[:2], 'hooks': hooks[:4], 'notes': notes[:3]}
