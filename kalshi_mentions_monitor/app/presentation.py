from __future__ import annotations

from .analysis_models import StrikeRankItem


def status_class(item: dict | StrikeRankItem) -> str:
    edge = str(getattr(item, 'edge_tag', None) or item.get('edge_tag') or '').lower()
    band = str(getattr(item, 'priority_band', None) or item.get('priority_band') or '').lower()
    if edge in {'рынок может переоценивать', 'требует осторожности'}:
        return 'status-red'
    if band in {'проверить сначала'} or edge in {'стоит проверить'}:
        return 'status-green'
    if band in {'проверить после', 'держать в поле зрения'} or edge in {'рабочая идея', 'погранично', 'осторожно'}:
        return 'status-yellow'
    return 'status-gray'


def type_class(strike_type: str) -> str:
    t = (strike_type or '').lower()
    if t in {'baseline speech', 'theme-linked'}:
        return 'type-blue'
    if t in {'odd tail'}:
        return 'type-gray'
    if t in {'special rule', 'nqe'}:
        return 'type-red'
    if t in {'qa-sensitive'}:
        return 'type-yellow'
    if t in {'game-state', 'broadcast-flow'}:
        return 'type-green'
    return 'type-gray'


def enrich_rank_item(item: dict) -> StrikeRankItem:
    return StrikeRankItem(
        market_id=item['market_id'],
        label=item['label'],
        display_label=item['display_label'],
        score=item['score'],
        priority_band=item['priority_band'],
        edge_tag=item['edge_tag'],
        strike_type=item['strike_type'],
        yes_reference_price=item['yes_reference_price'],
        price_bucket=item['price_bucket'],
        reasons=item.get('reasons', []),
        status_class=status_class(item),
        type_class=type_class(str(item.get('strike_type') or '')),
    )
