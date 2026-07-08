"""Pure, deterministic rate suggestion — no LLM call, no live rate API (per
2026-07 research: no free live rate API exists for freelance work). Bands
sourced from the Jobbers.io Global Rate Index, YunoJuno's 2026 Rates Report,
and davidmasse/freelancer-rates; refresh by hand periodically, don't invent
a live-query mechanism for it.

NEVER inject this into outreach/proposal text directly — the writer's
"let's discuss scope first, no price in message one" rule stays as-is.
This is for internal/dashboard reference only.
"""

RATE_BANDS_USD_PER_HR = {
    "agentic_ai": (60, 95),
    "full_stack": (40, 70),
}

HIGH_RATE_GEOGRAPHIES = {
    "us", "usa", "united states",
    "uk", "united kingdom",
    "canada", "australia",
    "eu", "europe", "germany", "netherlands", "uae",
}

GEOGRAPHY_MULTIPLIER = {
    "high": 1.0,
    "other": 0.6,
}


def _tier_for(client_geography: str) -> str:
    return "high" if client_geography.strip().lower() in HIGH_RATE_GEOGRAPHIES else "other"


def suggest_rate(is_agentic: bool, client_geography: str = "") -> dict:
    band = RATE_BANDS_USD_PER_HR["agentic_ai" if is_agentic else "full_stack"]
    tier = _tier_for(client_geography)
    mult = GEOGRAPHY_MULTIPLIER[tier]
    low, high = round(band[0] * mult), round(band[1] * mult)
    return {
        "suggested_rate_usd_per_hr": (low, high),
        "tier": tier,
        "justification": (
            f"{'Agentic AI' if is_agentic else 'Full-stack'} work, "
            f"{'high-rate' if tier == 'high' else 'other'}-tier client geography "
            f"({client_geography or 'unknown'}) — 2026 global freelance rate benchmark."
        ),
    }
