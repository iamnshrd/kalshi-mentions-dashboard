from __future__ import annotations

import html


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else '-'))


def render_list(items: list[str]) -> str:
    if not items:
        return '<li class="muted">—</li>'
    return ''.join(f'<li>{esc(x)}</li>' for x in items)


def render_rank_items(items: list[dict]) -> str:
    if not items:
        return '<li class="muted">—</li>'
    out = []
    for item in items:
        reasons = '; '.join(item.get('reasons', [])) or '—'
        display = item.get('display_label') or item.get('label')
        status_class = item.get('status_class', 'status-gray')
        type_class = item.get('type_class', 'type-gray')
        out.append(
            f'<li class="rank-item {status_class}">'
            f"<strong>{esc(display)}</strong> "
            f"<span class='pill type-pill {type_class}'>{esc(item.get('strike_type'))}</span> "
            f"<span class='pill {status_class}'>{esc(item.get('priority_band'))}</span> "
            f"<span class='pill edge {status_class}'>{esc(item.get('edge_tag'))}</span> "
            f"<span class='muted'>score {item.get('score')}</span><br>"
            f"<span class='muted'>{esc(reasons)}</span>"
            '</li>'
        )
    return ''.join(out)


def render_market_rows(summary: dict) -> str:
    ranking = {item.get('market_id'): item for item in summary.get('strike_priority', {}).get('full_ranking', [])}
    rows = []
    for bucket_name in ['structural', 'qa_sensitive', 'contextual', 'game_state_sensitive', 'likely_trap']:
        for item in summary.get('strike_intel', {}).get(bucket_name, []):
            ranked = ranking.get(item.get('market_id'), {})
            status_class = ranked.get('status_class', 'status-gray')
            type_class = ranked.get('type_class', 'type-gray')
            rows.append(
                f'<div class="market-row {status_class}">'
                '<div class="market-main">'
                f"<div class='market-title'>{esc(item.get('label'))}</div>"
                f"<div class='market-note'>{esc(item.get('note'))}</div>"
                '</div>'
                '<div class="market-meta">'
                f"<span class='pill type-pill {type_class}'>{esc(ranked.get('strike_type', '—'))}</span>"
                f"<span class='pill {status_class}'>{esc(ranked.get('priority_band', '—'))}</span>"
                f"<span class='pill edge {status_class}'>{esc(ranked.get('edge_tag', '—'))}</span>"
                '</div>'
                '</div>'
            )
    if not rows:
        rows = ['<div class="market-row status-gray"><div class="market-main">' f"<div class='market-title'>{esc(label)}</div>" '</div></div>' for label in summary.get('strike_codes', [])]
    return ''.join(rows)
