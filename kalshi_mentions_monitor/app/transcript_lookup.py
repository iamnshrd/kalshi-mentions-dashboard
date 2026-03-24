from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from .models import Classification
from .speaker_normalization import normalize_speaker_name


KEYWORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z'\-/]{2,}")
STOP = {
    'what', 'will', 'during', 'next', 'from', 'that', 'with', 'have', 'this', 'there', 'their', 'about',
    'would', 'could', 'should', 'after', 'before', 'they', 'them', 'your', 'into', 'because', 'while',
    'opening', 'remarks', 'say', 'says', 'said', 'market', 'markets', 'event', 'does', 'qualify'
}


def _extract_keywords(text: str, limit: int = 8) -> list[str]:
    words = []
    for w in KEYWORD_PATTERN.findall((text or '').lower()):
        if w in STOP or len(w) < 3:
            continue
        if w not in words:
            words.append(w)
        if len(words) >= limit:
            break
    return words


def _snippet(text: str, keywords: list[str]) -> str:
    low = text.lower()
    for kw in keywords:
        idx = low.find(kw.lower())
        if idx >= 0:
            start = max(0, idx - 120)
            end = min(len(text), idx + 220)
            return text[start:end].replace('\n', ' ').strip()
    return text[:220].replace('\n', ' ').strip()


def lookup_relevant_transcripts(db_path: Path, event_title: str, classification: Classification | None, speaker: str, limit: int = 5) -> list[dict]:
    if not db_path.exists():
        return []

    speaker_key = normalize_speaker_name(speaker)
    if not speaker_key or speaker_key == 'unknown':
        return []

    query_text = f"{event_title} {speaker} {(classification.market_group if classification else '')} {(classification.market_subtype if classification else '')}"
    keywords = _extract_keywords(query_text, limit=10)
    subtype_l = (classification.market_subtype if classification else '').lower()
    group_l = (classification.market_group if classification else '').lower()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        corpus = conn.execute(
            'SELECT speaker_key, speaker_name, transcript_count, total_chars, combined_text, source_files_json, event_hints_json FROM speaker_corpora WHERE speaker_key = ?',
            (speaker_key,),
        ).fetchone()
        if not corpus:
            return []

        corpus_text = corpus['combined_text'] or ''
        corpus_low = corpus_text.lower()
        corpus_score = 10
        corpus_score += min(sum(1 for kw in keywords if kw in corpus_low), 10)
        if subtype_l and subtype_l in corpus_low:
            corpus_score += 2
        if group_l and any(x in corpus_low for x in group_l.split('_')):
            corpus_score += 1

        files = json.loads(corpus['source_files_json'] or '[]')
        event_hints = json.loads(corpus['event_hints_json'] or '[]')
        rows = conn.execute(
            'SELECT filename, source_path, speaker_key, event_hint, text_content FROM transcripts WHERE speaker_key = ? ORDER BY filename',
            (speaker_key,),
        ).fetchall()

        scored = []
        for row in rows:
            text = row['text_content'] or ''
            low = text.lower()
            score = 10
            kw_hits = sum(1 for kw in keywords if kw in low)
            score += min(kw_hits, 6)
            if subtype_l and subtype_l in low:
                score += 2
            if group_l and any(x in low for x in group_l.split('_')):
                score += 1
            scored.append({
                'filename': row['filename'],
                'source_path': row['source_path'],
                'speaker_key': row['speaker_key'],
                'event_hint': row['event_hint'],
                'score': score,
                'keywords': keywords[:6],
                'snippet': _snippet(text, keywords[:6]),
            })
        scored.sort(key=lambda x: (-x['score'], x['filename']))

        return [{
            'match_type': 'speaker_corpus',
            'speaker_key': corpus['speaker_key'],
            'speaker_name': corpus['speaker_name'],
            'transcript_count': corpus['transcript_count'],
            'total_chars': corpus['total_chars'],
            'event_hints': event_hints,
            'source_files': files[:10],
            'score': corpus_score,
            'snippet': _snippet(corpus_text, keywords[:6]),
        }, *scored[:limit]]
    finally:
        conn.close()
