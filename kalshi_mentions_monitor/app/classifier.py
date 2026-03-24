from __future__ import annotations

from .models import Classification, NormalizedMarket
from .filtering import normalize_text


def classify_market(market: NormalizedMarket) -> Classification:
    text = normalize_text(market.title, market.subtitle, market.rules_primary, market.rules_secondary, market.event_ticker)
    reasoning: list[str] = []

    group = "unclear_or_special"
    subtype = "unknown"
    recurring = "one_off"
    phase = "unknown"
    context = "medium"
    rules_risk = "low"
    confidence = 0.55

    if any(x in text for x in ["trump", "vance", "white house", "senate", "congress", "governor", "president", "vice president", "secretary"]):
        group = "political_mentions"
        confidence = 0.88
        context = "high"
        recurring = "semi_recurring"
        reasoning.append("Detected political actor keywords")
        if "rally" in text:
            subtype = "rally"
            phase = "mixed"
            recurring = "recurring"
            reasoning.append("Rally-style event detected")
        elif any(x in text for x in ["press conference", "press briefing", "remarks"]):
            subtype = "press_conference"
            phase = "mixed"
            reasoning.append("Press/remarks style event detected")
        elif "interview" in text:
            subtype = "interview"
            phase = "mixed"
            reasoning.append("Interview format detected")
        elif any(x in text for x in ["hearing", "committee"]):
            subtype = "hearing"
            phase = "qa_heavy"
            reasoning.append("Hearing format detected")
        else:
            subtype = "speech"
            phase = "opening_heavy"
            reasoning.append("Defaulted to speech-style political event")

    elif any(x in text for x in ["earnings call", "investor day", "guidance", "ceo", "cfo", "quarterly", "conference"]):
        group = "earnings_or_corporate_mentions"
        subtype = "earnings_call" if "earnings" in text else "corporate_event"
        recurring = "semi_recurring"
        phase = "mixed"
        context = "medium"
        confidence = 0.84
        reasoning.append("Detected corporate/earnings keywords")

    elif any(x in text for x in ["during the game", "during the broadcast", "announcer", "commentator", "halftime show", "pregame", "postgame"]):
        group = "sports_announcer_mentions"
        recurring = "recurring"
        phase = "game_state_dependent"
        context = "medium"
        confidence = 0.9
        reasoning.append("Detected sports broadcast phrasing")
        if "pregame" in text:
            subtype = "pregame_show"
        elif "postgame" in text:
            subtype = "postgame_show"
        elif "halftime" in text:
            subtype = "halftime_show"
        else:
            subtype = "announcer_game_market"

    elif any(x in text for x in ["oscars", "grammys", "awards", "ceremony", "performance", "host", "red carpet", "show"]):
        group = "culture_entertainment_mentions"
        recurring = "one_off"
        phase = "segment_dependent"
        context = "high"
        confidence = 0.82
        reasoning.append("Detected entertainment/culture keywords")
        if "awards" in text or "oscars" in text or "grammys" in text:
            subtype = "awards_broadcast"
        elif "performance" in text:
            subtype = "performer_market"
        else:
            subtype = "live_show"

    # recurring overrides
    if any(x in text for x in ["fomc", "powell", "earnings call", "during the game", "announcer"]):
        recurring = "recurring"
        reasoning.append("Recurring-format hint detected")

    # phase heuristics
    if any(x in text for x in ["q&a", "questions"]):
        phase = "qa_heavy"
        reasoning.append("Q&A-specific phrasing detected")
    elif any(x in text for x in ["during remarks", "opening remarks", "speech"]):
        phase = "opening_heavy" if phase == "unknown" else phase

    # rules risk heuristics
    if any(x in text for x in ["translator", "translation", "translated"]):
        rules_risk = "high"
        confidence -= 0.05
        reasoning.append("Translator risk detected")
    if any(x in text for x in ["brand", "product", "service", "specifically advertised"]):
        rules_risk = "high"
        reasoning.append("Brand/product ambiguity risk detected")
    if any(x in text for x in ["compound", "hyphen", "exact phrase"]):
        rules_risk = "medium"
        reasoning.append("Exact wording / morphology sensitivity detected")
    if group == "unclear_or_special":
        rules_risk = "medium"
        reasoning.append("Unable to classify confidently; special handling recommended")

    return Classification(
        market_id=market.market_id,
        market_group=group,
        market_subtype=subtype,
        recurring_type=recurring,
        phase_profile=phase,
        context_sensitivity=context,
        rules_risk=rules_risk,
        classification_confidence=round(max(0.05, min(confidence, 0.99)), 2),
        reasoning=reasoning,
    )
