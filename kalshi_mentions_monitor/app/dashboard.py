from __future__ import annotations

import json
import re
from pathlib import Path

from .dashboard_sections import esc, render_list, render_market_rows, render_rank_items


def _slugify(value: str) -> str:
    value = (value or '').lower().strip()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    return value.strip('-')[:100] or 'event'


def _render_semantic_families(families: list[dict]) -> str:
    if not families:
        return '<li class="muted">—</li>'
    out = []
    for family in families:
        out.append(f"<li><strong>{esc(family.get('family'))}</strong>: {esc(', '.join(family.get('labels', [])))}</li>")
    return ''.join(out)


def _render_phase_fit(summary: dict) -> str:
    analyses = summary.get('strike_analyses', [])
    if not analyses:
        return '<li class="muted">—</li>'
    analyses = sorted(analyses, key=lambda x: (-x.get('rank', {}).get('score', 0), x.get('label', '')))[:8]
    out = []
    for item in analyses:
        alloc = item.get('attention_allocation', '-')
        out.append(f"<li><strong>{esc(item.get('label'))}</strong>: {esc(item.get('phase_fit'))} · {esc(alloc)}</li>")
    return ''.join(out)


def _page_shell(title: str, body: str) -> str:
    return f'''<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>
    :root {{ color-scheme: dark; }}
    body {{ font-family: Inter, ui-sans-serif, system-ui, sans-serif; margin: 0; background: #0b1020; color: #e7ecf5; }}
    a {{ color: #8cc8ff; text-decoration: none; }} a:hover {{ text-decoration: underline; }}
    .wrap {{ max-width: 1240px; margin: 0 auto; padding: 24px; }} .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }}
    .card {{ background: #141a2e; border: 1px solid #23304f; border-radius: 14px; padding: 16px; box-shadow: 0 6px 20px rgba(0,0,0,.2); }} .hero {{ margin-bottom: 18px; }} .muted {{ color: #9fb0cf; }}
    .pill {{ display: inline-block; padding: 2px 8px; border-radius: 999px; background: #23304f; font-size: 12px; margin-right: 6px; border: 1px solid transparent; }} .edge {{ background: #2f3d67; }} .type-pill {{ background: #1a2238; color: #d5def0; }}
    .type-blue {{ background: #172f56; color: #9fcbff; }} .type-green {{ background: #163929; color: #8be0af; }} .type-yellow {{ background: #473814; color: #ffd86b; }} .type-gray {{ background: #2a3142; color: #b8c3db; }} .type-red {{ background: #4a1f1f; color: #ff9b9b; }}
    .status-green {{ border-color: #245b3b !important; }} .status-yellow {{ border-color: #7c6422 !important; }} .status-gray {{ border-color: #3a4254 !important; }} .status-red {{ border-color: #7a2d2d !important; }}
    .pill.status-green {{ background: #183824; color: #9af0b6; }} .pill.status-yellow {{ background: #433515; color: #ffd86b; }} .pill.status-gray {{ background: #2a3142; color: #b8c3db; }} .pill.status-red {{ background: #4a1f1f; color: #ff9b9b; }}
    h1, h2, h3 {{ margin: 0 0 10px; }} ul {{ margin: 8px 0 0 18px; padding: 0; }} li {{ margin: 6px 0; }} .rank-item {{ padding: 8px 10px; border: 1px solid #23304f; border-radius: 10px; margin-bottom: 10px; list-style: none; }}
    .event-link {{ display: block; color: inherit; text-decoration: none; }} .row {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 8px 0 0; }} .stat {{ background: #10182d; border: 1px solid #23304f; border-radius: 10px; padding: 8px 10px; }} .section {{ margin-top: 18px; }} .two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }} .three {{ display: grid; grid-template-columns: 1.2fr .9fr .9fr; gap: 16px; }}
    .market-list {{ margin-top: 8px; border-top: 1px solid #23304f; }} .market-row {{ display: flex; justify-content: space-between; gap: 16px; padding: 12px 0; border-bottom: 1px solid #23304f; border-left: 4px solid transparent; padding-left: 12px; }}
    .market-row.status-green {{ border-left-color: #2fb36d; background: rgba(47,179,109,.05); }} .market-row.status-yellow {{ border-left-color: #e0b84e; background: rgba(224,184,78,.05); }} .market-row.status-gray {{ border-left-color: #74819b; background: rgba(116,129,155,.04); }} .market-row.status-red {{ border-left-color: #d95c5c; background: rgba(217,92,92,.06); }}
    .market-main {{ min-width: 0; }} .market-title {{ font-weight: 700; }} .market-note {{ color: #9fb0cf; margin-top: 4px; font-size: 14px; line-height: 1.35; }} .market-meta {{ white-space: nowrap; align-self: center; }} .legend {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }}
    @media (max-width: 1000px) {{ .three {{ grid-template-columns: 1fr; }} .market-meta {{ white-space: normal; }} .market-row {{ flex-direction: column; }} }} @media (max-width: 900px) {{ .two {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body><div class="wrap">{body}</div></body></html>'''


def render_event_page(summary: dict, event_pages_dir: Path) -> str:
    rank = summary.get('strike_priority', {})
    attention = summary.get('attention_allocation', {})
    title = summary.get('event_title') or summary.get('group_key') or 'Событие'
    body = f'''
    <div class="hero"><div><a href="../index.html">← Назад к дашборду</a></div><h1>{esc(title)}</h1>
    <div class="row"><div class="stat">Группа: <strong>{esc(summary.get('dominant_group'))}</strong></div><div class="stat">Подтип: <strong>{esc(summary.get('dominant_subtype'))}</strong></div><div class="stat">Спикер: <strong>{esc(summary.get('speaker'))}</strong></div><div class="stat">Приоритет внимания: <strong>{esc(summary.get('priority'))}</strong></div><div class="stat">Страйков: <strong>{esc(summary.get('market_count'))}</strong></div></div>
    <div class="legend"><span class='pill status-green'>зелёный = проверить сначала</span><span class='pill status-yellow'>жёлтый = держать в поле зрения</span><span class='pill status-gray'>серый = можно отложить</span><span class='pill status-red'>красный = рынок может переоценивать / нужна осторожность</span></div>
    <div class="legend"><span class='pill type-pill type-blue'>baseline speech / theme-linked</span><span class='pill type-pill type-yellow'>qa-sensitive</span><span class='pill type-pill type-green'>game-state / broadcast-flow</span><span class='pill type-pill type-gray'>odd tail</span><span class='pill type-pill type-red'>special rule / NQE</span></div></div>
    <div class="section card"><h2>Attention allocation</h2><div class="row"><div class="stat">Prep: <strong>{esc(attention.get('prep_allocation'))}</strong></div><div class="stat">Live: <strong>{esc(attention.get('live_allocation'))}</strong></div></div><p class="muted">{esc(attention.get('summary'))}</p></div>
    <div class="section card"><div class="market-list">{render_market_rows(summary)}</div></div>
    <div class="three section"><div class="card"><h2>С чего начать проверку</h2><p>{esc(summary.get('prep_focus'))}</p><h3 class="section">Что проверить до события</h3><ul>{render_list(summary.get('context_checks', []))}</ul></div><div class="card"><h2>Что проверить первым</h2><ul>{render_rank_items(rank.get('top_watchlist', []))}</ul></div><div class="card"><h2>Где рынок может ошибаться</h2><ul>{render_rank_items(rank.get('likely_overreactions', []))}</ul></div></div>
    <div class="two section"><div class="card"><h2>Manual trader prompts</h2><ul>{render_list(summary.get('manual_trader_prompts', []))}</ul></div><div class="card"><h2>Что пока можно отложить</h2><ul>{render_rank_items(rank.get('low_priority_strikes', []))}</ul></div></div>
    <div class="two section"><div class="card"><h2>Какая история реально полезна</h2><ul>{render_list(summary.get('relevant_history_notes', []))}</ul></div><div class="card"><h2>Где consensus может читать рынок неправильно</h2><ul>{render_list(summary.get('consensus_misread', []))}</ul></div></div>
    <div class="two section"><div class="card"><h2>Phase fit по страйкам</h2><ul>{_render_phase_fit(summary)}</ul></div><div class="card"><h2>Semantic families</h2><ul>{_render_semantic_families(summary.get('semantic_families', []))}</ul></div></div>
    <!-- transcript layer frozen for now; hidden from dashboard until reprioritized -->
    <div class="two section"><div class="card"><h2>План на opening</h2><ul>{render_list(summary.get('opening_plan', []))}</ul></div><div class="card"><h2>После opening / Q&A</h2><ul>{render_list(summary.get('post_opening_plan', []))}</ul><h3 class="section">Переход в Q&A</h3><ul>{render_list(summary.get('qa_transition_plan', []))}</ul></div></div>
    <div class="two section"><div class="card"><h2>Подготовка до события</h2><ul>{render_list(summary.get('pre_event_summary', []))}</ul></div><div class="card"><h2>Лайв-ориентиры</h2><ul>{render_list(summary.get('live_trading_summary', []))}</ul></div></div>
    <div class="two section"><div class="card"><h2>Риски и caveats</h2><ul>{render_list(summary.get('risk_summary', []))}</ul></div><div class="card"><h2>Контекстные заметки</h2><ul>{render_list(summary.get('context_notes', []))}</ul></div></div>
    '''
    return _page_shell(title, body)


def _miniapp_html() -> str:
    return '''<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Mentions Mini App</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0b1020;
      --card: #141a2e;
      --border: #23304f;
      --text: #e7ecf5;
      --muted: #9fb0cf;
      --green: #183824;
      --green-text: #9af0b6;
      --yellow: #433515;
      --yellow-text: #ffd86b;
      --red: #4a1f1f;
      --red-text: #ff9b9b;
      --gray: #2a3142;
      --gray-text: #b8c3db;
      --blue: #172f56;
      --blue-text: #9fcbff;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--text); font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
    .app { max-width: 720px; margin: 0 auto; padding: 14px 14px 32px; }
    .top { position: sticky; top: 0; z-index: 5; background: linear-gradient(180deg, rgba(11,16,32,.98), rgba(11,16,32,.92)); backdrop-filter: blur(8px); padding: 8px 0 12px; }
    h1,h2,h3,p { margin: 0; }
    .muted { color: var(--muted); }
    .search { margin-top: 10px; width: 100%; background: #10182d; color: var(--text); border: 1px solid var(--border); border-radius: 14px; padding: 12px 14px; font-size: 16px; }
    .list, .detail { display: grid; gap: 12px; margin-top: 14px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 14px; box-shadow: 0 6px 20px rgba(0,0,0,.18); }
    .event-card { cursor: pointer; }
    .title { font-size: 18px; font-weight: 700; line-height: 1.2; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
    .pill { display: inline-block; padding: 4px 8px; border-radius: 999px; background: var(--gray); color: var(--gray-text); font-size: 12px; }
    .pill.green { background: var(--green); color: var(--green-text); }
    .pill.yellow { background: var(--yellow); color: var(--yellow-text); }
    .pill.red { background: var(--red); color: var(--red-text); }
    .pill.blue { background: var(--blue); color: var(--blue-text); }
    .section-title { font-size: 15px; font-weight: 700; margin-bottom: 8px; }
    .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .stat { background: #10182d; border: 1px solid var(--border); border-radius: 12px; padding: 10px; }
    .market { padding: 12px 0; border-bottom: 1px solid var(--border); }
    .market:last-child { border-bottom: 0; }
    .market-title { font-weight: 700; }
    .market-note { color: var(--muted); margin-top: 4px; font-size: 14px; }
    .back { display: inline-flex; align-items: center; gap: 8px; border: 1px solid var(--border); background: #10182d; color: var(--text); border-radius: 12px; padding: 10px 12px; cursor: pointer; }
    .hidden { display: none !important; }
    .kv { display: grid; gap: 6px; margin-top: 8px; }
    .kv div { color: var(--muted); }
    ul { margin: 0; padding-left: 18px; }
    li { margin: 6px 0; }
  </style>
</head>
<body>
  <div class="app">
    <div id="listView">
      <div class="top">
        <h1>Mentions Mini App</h1>
        <p class="muted">События и быстрый разбор внутри Telegram.</p>
        <input id="search" class="search" placeholder="Поиск по событию, спикеру, группе..." />
      </div>
      <div id="eventsCount" class="muted" style="margin-top:12px"></div>
      <div id="eventsList" class="list"></div>
    </div>
    <div id="detailView" class="hidden">
      <div class="top">
        <button id="backBtn" class="back">← Назад</button>
      </div>
      <div id="detail" class="detail"></div>
    </div>
  </div>
<script>
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  tg.setHeaderColor('#0b1020');
  tg.setBackgroundColor('#0b1020');
}

const state = { events: [], filtered: [], current: null };

function esc(s) {
  return String(s ?? '-').replace(/[&<>\"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}
function pillClass(priority) {
  const p = String(priority || '').toLowerCase();
  if (p.includes('high') || p.includes('сначала')) return 'green';
  if (p.includes('после') || p.includes('норм')) return 'yellow';
  if (p.includes('осторож') || p.includes('red')) return 'red';
  return 'blue';
}
function renderEventCard(item) {
  const top = (item.strike_priority?.top_watchlist || []).slice(0,3).map(x => x.display_label || x.label).join(', ') || '—';
  const prep = item.attention_allocation?.prep_allocation || '-';
  const live = item.attention_allocation?.live_allocation || '-';
  return `<div class="card event-card" data-slug="${esc(item.slug)}">
    <div class="title">${esc(item.event_title)}</div>
    <div class="row">
      <span class="pill blue">${esc(item.dominant_group)}</span>
      <span class="pill blue">${esc(item.dominant_subtype)}</span>
      <span class="pill ${pillClass(item.priority)}">${esc(item.priority)}</span>
    </div>
    <div class="kv">
      <div>Спикер: <strong>${esc(item.speaker)}</strong></div>
      <div>Страйков: <strong>${esc(item.market_count)}</strong></div>
      <div>Prep: <strong>${esc(prep)}</strong> · Live: <strong>${esc(live)}</strong></div>
      <div>Смотреть первым: <strong>${esc(top)}</strong></div>
    </div>
  </div>`;
}
function renderMarket(item) {
  const rank = item.rank || {};
  return `<div class="market">
    <div class="market-title">${esc(item.label)}</div>
    <div class="market-note">${esc(item.note || '-')}</div>
    <div class="row">
      <span class="pill blue">${esc(rank.strike_type || '-')}</span>
      <span class="pill ${pillClass(rank.priority_band)}">${esc(rank.priority_band || '-')}</span>
      <span class="pill ${pillClass(rank.edge_tag)}">${esc(rank.edge_tag || '-')}</span>
    </div>
  </div>`;
}
function renderRank(items) {
  if (!items || !items.length) return '<div class="muted">—</div>';
  return items.slice(0,5).map(item => `<div class="market"><div class="market-title">${esc(item.display_label || item.label)}</div><div class="market-note">${esc((item.reasons || []).join(' · ') || '—')}</div></div>`).join('');
}
function showList() {
  document.getElementById('detailView').classList.add('hidden');
  document.getElementById('listView').classList.remove('hidden');
  if (tg?.BackButton) tg.BackButton.hide();
  history.replaceState({}, '', './index.html');
}
function showDetail(slug) {
  const item = state.events.find(x => x.slug === slug);
  if (!item) return;
  state.current = item;
  document.getElementById('listView').classList.add('hidden');
  document.getElementById('detailView').classList.remove('hidden');
  if (tg?.BackButton) { tg.BackButton.show(); tg.BackButton.onClick(showList); }
  history.replaceState({}, '', `./index.html#${encodeURIComponent(slug)}`);
  const markets = (item.strike_analyses || []).map(renderMarket).join('');
  document.getElementById('detail').innerHTML = `
    <div class="card">
      <div class="title">${esc(item.event_title)}</div>
      <div class="row">
        <span class="pill blue">${esc(item.dominant_group)}</span>
        <span class="pill blue">${esc(item.dominant_subtype)}</span>
        <span class="pill ${pillClass(item.priority)}">${esc(item.priority)}</span>
      </div>
      <div class="kv">
        <div>Спикер: <strong>${esc(item.speaker)}</strong></div>
        <div>Страйков: <strong>${esc(item.market_count)}</strong></div>
        <div>Prep: <strong>${esc(item.attention_allocation?.prep_allocation || '-')}</strong></div>
        <div>Live: <strong>${esc(item.attention_allocation?.live_allocation || '-')}</strong></div>
      </div>
    </div>
    <div class="card"><div class="section-title">С чего начать</div><div class="muted">${esc(item.prep_focus || '-')}</div></div>
    <div class="card"><div class="section-title">Страйки события</div>${markets || '<div class="muted">—</div>'}</div>
    <div class="card"><div class="section-title">Что проверить первым</div>${renderRank(item.strike_priority?.top_watchlist)}</div>
    <div class="card"><div class="section-title">Где рынок может ошибаться</div><ul>${(item.consensus_misread || []).map(x => `<li>${esc(x)}</li>`).join('') || '<li>—</li>'}</ul></div>
    <div class="card"><div class="section-title">Opening / Q&A план</div><ul>${(item.opening_plan || []).slice(0,2).map(x => `<li>${esc(x)}</li>`).join('')}</ul><ul>${(item.qa_transition_plan || []).slice(0,2).map(x => `<li>${esc(x)}</li>`).join('')}</ul></div>
  `;
}
function applyFilter(q) {
  const query = String(q || '').toLowerCase().trim();
  state.filtered = !query ? [...state.events] : state.events.filter(item => {
    const hay = [item.event_title, item.speaker, item.dominant_group, item.dominant_subtype, ...(item.strike_codes || [])].join(' ').toLowerCase();
    return hay.includes(query);
  });
  document.getElementById('eventsCount').textContent = `Событий: ${state.filtered.length}`;
  document.getElementById('eventsList').innerHTML = state.filtered.map(renderEventCard).join('') || '<div class="card muted">Ничего не найдено.</div>';
  document.querySelectorAll('.event-card').forEach(el => el.addEventListener('click', () => showDetail(el.dataset.slug)));
}
async function boot() {
  const res = await fetch('./data/events.json');
  const data = await res.json();
  state.events = data.events || [];
  applyFilter('');
  const hash = decodeURIComponent((location.hash || '').replace(/^#/, ''));
  if (hash) showDetail(hash);
}
document.getElementById('search').addEventListener('input', (e) => applyFilter(e.target.value));
document.getElementById('backBtn').addEventListener('click', showList);
boot();
</script>
</body>
</html>'''


def _write_miniapp(dashboard_dir: Path, summaries: list[dict]) -> Path:
    miniapp_dir = dashboard_dir / 'miniapp'
    data_dir = miniapp_dir / 'data'
    miniapp_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    payload_events = []
    for summary in summaries:
        data = dict(summary)
        data['slug'] = _slugify(summary.get('event_title') or summary.get('group_key') or 'event')
        payload_events.append(data)

    (data_dir / 'events.json').write_text(json.dumps({'events': payload_events}, ensure_ascii=False, indent=2), encoding='utf-8')
    index_path = miniapp_dir / 'index.html'
    index_path.write_text(_miniapp_html(), encoding='utf-8')
    return index_path


def render_dashboard(output_dir: Path) -> tuple[Path, int]:
    events_json_dir = output_dir / 'events' / 'json'
    dashboard_dir = output_dir / 'dashboard'
    event_pages_dir = dashboard_dir / 'events'
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    event_pages_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    for path in sorted(events_json_dir.glob('*.json')):
        try:
            summaries.append(json.loads(path.read_text(encoding='utf-8')))
        except Exception:
            continue
    cards = []
    for summary in sorted(summaries, key=lambda s: ((s.get('priority') != 'high'), s.get('open_time') or '', s.get('event_title') or '')):
        slug = _slugify(summary.get('event_title') or summary.get('group_key') or 'event')
        (event_pages_dir / f'{slug}.html').write_text(render_event_page(summary, event_pages_dir), encoding='utf-8')
        top = summary.get('strike_priority', {}).get('top_watchlist', [])[:3]
        top_text = ', '.join(item.get('display_label') or item.get('label', '?') for item in top) or '—'
        alloc = summary.get('attention_allocation', {})
        cards.append('<div class="card">' f"<a class='event-link' href='events/{esc(slug)}.html'>" f"<h2>{esc(summary.get('event_title'))}</h2>" f"<div class='row'><span class='pill'>{esc(summary.get('dominant_group'))}</span><span class='pill'>{esc(summary.get('dominant_subtype'))}</span><span class='pill'>{esc(summary.get('priority'))}</span></div>" f"<p class='muted'>Спикер: {esc(summary.get('speaker'))} · Страйков: {esc(summary.get('market_count'))}</p>" f"<p><strong>Prep:</strong> {esc(alloc.get('prep_allocation'))} · <strong>Live:</strong> {esc(alloc.get('live_allocation'))}</p>" f"<p><strong>Проверить первым:</strong> {esc(top_text)}</p>" '</a></div>')
    body = f'''<div class="hero"><h1>Kalshi Mentions Dashboard</h1><p class="muted">Вспомогательный событийный дашборд: помогает быстро проверить контекст, страйки и лайв-фазы, но не заменяет ручное решение трейдера.</p><div class="row"><div class="stat">Событий: <strong>{len(summaries)}</strong></div><div class="stat"><a href="miniapp/index.html">Открыть Telegram Mini App view</a></div></div></div><div class="grid">{''.join(cards) if cards else '<div class="card"><p class="muted">Пока нет event summaries.</p></div>'}</div>'''
    index_path = dashboard_dir / 'index.html'
    index_path.write_text(_page_shell('Kalshi Mentions Dashboard', body), encoding='utf-8')
    _write_miniapp(dashboard_dir, summaries)
    return index_path, len(summaries)
