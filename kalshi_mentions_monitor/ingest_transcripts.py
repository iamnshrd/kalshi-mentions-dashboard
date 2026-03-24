from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kalshi_mentions_monitor.app.config import Settings
from kalshi_mentions_monitor.app.transcript_db import ensure_transcript_tables, ingest_transcript_file, rebuild_speaker_corpora


TEXT_EXTS = {'.txt', '.md', '.json', '.csv', '.text', '.log', '.rtf', '.xml', '.html', '.htm', '.tsv', '.yml', '.yaml', ''}


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python3 kalshi_mentions_monitor/ingest_transcripts.py <directory>')
    root = Path(sys.argv[1]).resolve()
    if not root.exists():
        raise SystemExit(f'Path does not exist: {root}')

    s = Settings()
    conn = sqlite3.connect(s.db_path)
    try:
        ensure_transcript_tables(conn)
        inserted = 0
        seen = 0
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTS:
                continue
            seen += 1
            try:
                if ingest_transcript_file(conn, path):
                    inserted += 1
            except Exception:
                continue
        corpora = rebuild_speaker_corpora(conn)
        total = conn.execute('SELECT COUNT(*) FROM transcripts').fetchone()[0]
        print(json.dumps({'files_seen': seen, 'inserted': inserted, 'total_transcripts': total, 'speaker_corpora': corpora}, ensure_ascii=False, indent=2))
    finally:
        conn.close()


if __name__ == '__main__':
    main()
