from __future__ import annotations

import re
from pathlib import Path

SPEAKER_ALIASES = {
    'melania trump': ['melania_trump', 'melania trump', 'melania'],
    'donald trump': ['donald_trump', 'president_trump', 'president trump', 'trump_', ' trump ', 'donald trump', 'donald j. trump', 'trump'],
    'karoline leavitt': ['karoline_leavitt', 'karoline leavitt', 'leavitt'],
    'gavin newsom': ['gavin_newsom', 'gavin newsom', 'newsom'],
    'kristi noem': ['kristi_noem', 'kristi noem', 'noem'],
    'keir starmer': ['keir_starmer', 'keir starmer', 'starmer'],
    'jerome powell': ['chair_powell', 'jerome powell', 'powell'],
    'foster': ['foster'],
    'logan': ['logan'],
    'nate': ['nate'],
    'tyrael': ['tyrael'],
}


def normalize_speaker_name(raw: str) -> str:
    low = (raw or '').lower().strip()
    for canon, aliases in SPEAKER_ALIASES.items():
        if low == canon or any(low == a for a in aliases):
            return canon
    return low


def _infer_from_filename(path: Path) -> str:
    name = path.stem.lower()
    prefix = '_'.join(name.split('_')[:3])
    for canon, aliases in SPEAKER_ALIASES.items():
        if any(alias in prefix for alias in aliases):
            return canon
    first = name.split('_')[0] if '_' in name else name.split()[0]
    for canon, aliases in SPEAKER_ALIASES.items():
        if any(first == alias.replace('_', ' ') or first == alias.split('_')[0] for alias in aliases):
            return canon
    return ''


def infer_speaker_from_path_and_text(path: Path, text: str) -> str:
    by_file = _infer_from_filename(path)
    if by_file:
        return by_file
    hay = f"{path.stem} {text[:1200]}".lower()
    for canon, aliases in SPEAKER_ALIASES.items():
        if any(alias.replace('_', ' ') in hay for alias in aliases):
            return canon
    return ''


def infer_event_hint(path: Path, text: str) -> str:
    head = (path.stem + ' ' + text[:500]).lower()
    for candidate in ['earnings', 'press conference', 'remarks', 'interview', 'pmq', 'hearing', 'super bowl', 'announcer', 'briefing']:
        if candidate in head:
            return candidate
    return ''


def filename_tokens(path: Path) -> list[str]:
    return [t for t in re.split(r'[^a-z0-9]+', path.stem.lower()) if t]
