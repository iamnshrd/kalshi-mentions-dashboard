from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from .speaker_normalization import infer_event_hint, infer_speaker_from_path_and_text


def ensure_transcript_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        '''
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_hash TEXT UNIQUE,
            source_path TEXT,
            filename TEXT,
            speaker_hint TEXT,
            speaker_key TEXT,
            event_hint TEXT,
            text_content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_transcripts_speaker_hint ON transcripts(speaker_hint);
        CREATE INDEX IF NOT EXISTS idx_transcripts_speaker_key ON transcripts(speaker_key);
        CREATE INDEX IF NOT EXISTS idx_transcripts_event_hint ON transcripts(event_hint);

        CREATE TABLE IF NOT EXISTS speaker_corpora (
            speaker_key TEXT PRIMARY KEY,
            speaker_name TEXT,
            transcript_count INTEGER NOT NULL DEFAULT 0,
            total_chars INTEGER NOT NULL DEFAULT 0,
            combined_text TEXT,
            source_files_json TEXT,
            event_hints_json TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        '''
    )
    conn.commit()


def ingest_transcript_file(conn: sqlite3.Connection, path: Path) -> bool:
    text = path.read_text(encoding='utf-8', errors='ignore')
    content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    speaker_key = infer_speaker_from_path_and_text(path, text)
    event_hint = infer_event_hint(path, text)
    cur = conn.execute(
        '''
        INSERT INTO transcripts (
            content_hash, source_path, filename, speaker_hint, speaker_key, event_hint, text_content
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(content_hash) DO UPDATE SET
            source_path=excluded.source_path,
            filename=excluded.filename,
            speaker_hint=excluded.speaker_hint,
            speaker_key=excluded.speaker_key,
            event_hint=excluded.event_hint,
            text_content=excluded.text_content
        ''',
        (content_hash, str(path), path.name, speaker_key, speaker_key, event_hint, text),
    )
    conn.commit()
    return cur.rowcount > 0


def rebuild_speaker_corpora(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        '''
        SELECT speaker_key, filename, source_path, event_hint, text_content
        FROM transcripts
        WHERE COALESCE(speaker_key, '') != ''
        ORDER BY speaker_key, filename
        '''
    ).fetchall()

    grouped: dict[str, dict] = {}
    for row in rows:
        key = row[0]
        grouped.setdefault(key, {
            'speaker_name': key,
            'files': [],
            'event_hints': [],
            'chunks': [],
        })
        grouped[key]['files'].append({'filename': row[1], 'source_path': row[2]})
        if row[3] and row[3] not in grouped[key]['event_hints']:
            grouped[key]['event_hints'].append(row[3])
        grouped[key]['chunks'].append(f"\n\n===== {row[1]} =====\n{row[4] or ''}")

    conn.execute('DELETE FROM speaker_corpora')
    for key, data in grouped.items():
        combined_text = ''.join(data['chunks'])
        conn.execute(
            '''
            INSERT INTO speaker_corpora (
                speaker_key, speaker_name, transcript_count, total_chars, combined_text, source_files_json, event_hints_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''',
            (
                key,
                data['speaker_name'],
                len(data['files']),
                len(combined_text),
                combined_text,
                json.dumps(data['files'], ensure_ascii=False),
                json.dumps(data['event_hints'], ensure_ascii=False),
            ),
        )
    conn.commit()
    return len(grouped)
