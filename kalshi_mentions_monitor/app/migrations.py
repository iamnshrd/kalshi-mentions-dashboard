from __future__ import annotations

import sqlite3

MIGRATIONS: list[tuple[str, list[str]]] = [
    (
        '001_init_meta',
        [
            'CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)'
        ],
    ),
    (
        '002_classifications_speaker_format_confidence',
        [
            'ALTER TABLE classifications ADD COLUMN speaker TEXT',
            'ALTER TABLE classifications ADD COLUMN format_confidence REAL',
        ],
    ),
]


def apply_migrations(conn: sqlite3.Connection) -> None:
    conn.execute('CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    applied = {row[0] for row in conn.execute('SELECT name FROM schema_migrations').fetchall()}
    for name, statements in MIGRATIONS:
        if name in applied:
            continue
        for stmt in statements:
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError as exc:
                msg = str(exc).lower()
                if 'duplicate column name' in msg or 'already exists' in msg:
                    continue
                raise
        conn.execute('INSERT OR IGNORE INTO schema_migrations (name) VALUES (?)', (name,))
    conn.commit()
