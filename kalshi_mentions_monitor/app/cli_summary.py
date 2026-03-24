from __future__ import annotations


def format_summary(result: dict) -> str:
    lines = [
        f"Fetched markets: {result.get('markets_fetched', 0)}",
        f"Mention candidates: {result.get('mention_candidates', 0)}",
        f"New markets found: {result.get('new_markets_found', 0)}",
    ]
    for item in result.get("new_markets", []):
        c = item.get("classification", {})
        lines.extend([
            "",
            f"- {item.get('title', item.get('market_id'))}",
            f"  group={c.get('market_group')} subtype={c.get('market_subtype')} phase={c.get('phase_profile')} rules={c.get('rules_risk')}",
            f"  report={item.get('markdown_path')}",
        ])
    return "\n".join(lines)
