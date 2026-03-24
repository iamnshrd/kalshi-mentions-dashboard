# Kalshi Mentions Monitor — V1 Scope

## V1 Definition

V1 = рабочий **mention prep copilot**.

Система должна:
- стабильно находить новые mention events в Kalshi,
- корректно раскладывать основные типы событий,
- давать полезный event-level prep/live helper analysis,
- давать usable strike-level ranking,
- быть доступной через dashboard и Telegram Mini App.

V1 **не** должна быть:
- fair value engine,
- pricing oracle,
- transcript-semantic engine,
- perfect real-time news terminal,
- fully polished Telegram product.

---

## In Scope for V1

### 1. Polling / ingestion / stability

Must have:
- polling Kalshi каждые 5 минут,
- один стабильный daemon,
- отсутствие stale-process corruption,
- автоматический rebuild output,
- auto-deploy dashboard/mini app.

Success criteria:
- новые `poll_runs` идут стабильно,
- новые mention events доходят до dashboard,
- классификации не откатываются в старые bucket’ы.

### 2. Core event classification

Must have:
- political mentions,
- civic/local politics,
- legal/court,
- earnings/corporate,
- sports announcers,
- podcast/stream,
- culture/entertainment.

Success criteria:
- очевидные кейсы не попадают в absurd routing,
- Zohran-like local politics не sports,
- TBPN-like podcast не sports,
- NBA announcers не NFL.

### 3. Event-level helper analytics

Must have:
- `prep_focus`,
- `live_focus`,
- `context_checks`,
- `consensus_misread`,
- `opening_plan`, `post_opening_plan`, `qa_transition_plan`,
- `attention_allocation`.

Success criteria:
- event page помогает быстро понять, как читать событие,
- аналитика helper-mode, а не oracle-mode.

### 4. Strike-level helper ranking

Must have:
- `top_watchlist`,
- `likely_overreactions`,
- `low_priority_strikes`,
- short strike notes,
- phase/lane logic,
- ranking alignment with strike notes.

Success criteria:
- страйки не выглядят одинаково,
- заметные lanes/tails/fragility отражены,
- ranking не спорит с краткими note’ами.

### 5. Russian dashboard + Mini App

Must have:
- dashboard на русском,
- Mini App открывается и usable,
- GitHub Pages publish работает,
- mobile-first reading path приемлемый.

Success criteria:
- можно реально пользоваться с телефона,
- нет embarrassing junk в публичном интерфейсе.

### 6. Current-context layer (moderate)

Must have:
- heuristic current context,
- selective real headlines for high-priority events,
- quality gate for low-quality headlines.

Success criteria:
- context section полезна,
- noisy headlines не лезут в UI,
- sports может оставаться heuristic-only, если source quality плохая.

---

## Explicitly Out of Scope for V1

### Not in V1
- transcript retrieval / transcript UI integration,
- perfect news retrieval / source graph / source trust system,
- price-aware fair value engine,
- Kelly sizing / trade automation,
- fully polished Telegram UX,
- exhaustive event taxonomy for every rare edge case,
- semantic search / embeddings stack.

These are **V2+** items.

---

## Remaining V1 Blockers

Only these should block V1 freeze:

1. Confirm daemon remains stable over time
2. Confirm Mini App reflects fresh data reliably
3. Remove the last obvious low-quality analytical outputs in major event families
4. Do one final V1 QA pass on real event pages

If these are done, V1 should freeze.

---

## Freeze Rule

Any new idea must answer:

**Does this fix a V1 blocker, or is it V2?**

If it does not fix a V1 blocker, it should not delay V1 freeze.

---

## V2 Candidate Bucket

Good ideas, but not V1 blockers:
- transcript intelligence revival,
- stronger sports news sourcing,
- better source-aware news ranking,
- richer cluster valuation,
- price-aware ranking,
- better Telegram-native controls,
- richer filters/search/navigation.
