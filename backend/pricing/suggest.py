"""Pure, deterministic rate suggestion — no LLM call, no live rate API (per
2026-07 research: no free live rate API exists for freelance work). Bands
sourced from the Jobbers.io Global Rate Index, YunoJuno's 2026 Rates Report,
and davidmasse/freelancer-rates; refresh by hand periodically, don't invent
a live-query mechanism for it.

NEVER inject this into outreach/proposal text directly — the writer's
"let's discuss scope first, no price in message one" rule stays as-is.
This is for internal/dashboard reference only.
"""

import re

RATE_BANDS_USD_PER_HR = {
    "agentic_ai": (60, 95),
    "full_stack": (40, 70),
}

# Tiering is an EXCEPTION LIST, not a rich-country whitelist. Roughly 120-130
# currencies are stronger than the rupee, so almost anywhere pays better than
# local work — a whitelist of Western countries silently discounted most of the
# world.
#
# It tracks prevailing DEV RATES, not exchange rates: the yen is "weaker" than
# the rupee per unit, yet Japanese rates are far higher. These are the markets
# where freelance software rates sit at or below India's, so the discounted band
# applies.
# Cities are listed alongside countries because a lead's location is whatever
# the source gave — often a bare city or street address, never a tidy
# "City, Country". A country-only list quoted a Delhi client the premium band.
LOWER_RATE_MARKETS = {
    # countries
    "india", "pakistan", "bangladesh", "nepal", "sri lanka", "bhutan", "myanmar",
    "afghanistan", "cambodia", "laos",
    "nigeria", "kenya", "ghana", "uganda", "tanzania", "ethiopia", "rwanda",
    "zimbabwe", "zambia", "mozambique", "cameroon", "senegal", "ivory coast",
    "bolivia", "venezuela", "nicaragua", "honduras",
    # their major cities
    "delhi", "new delhi", "mumbai", "bengaluru", "bangalore", "hyderabad",
    "chennai", "kolkata", "pune", "ahmedabad", "surat", "jaipur", "lucknow",
    "indore", "chandigarh", "kochi", "coimbatore", "nagpur", "bhopal",
    "gurugram", "gurgaon", "noida", "visakhapatnam", "thane", "vadodara",
    "karachi", "lahore", "islamabad", "dhaka", "chittagong", "kathmandu",
    "colombo", "yangon", "phnom penh",
    "lagos", "abuja", "nairobi", "mombasa", "accra", "kampala", "kigali",
    "dar es salaam", "addis ababa", "harare", "lusaka",
}

# Anything clearly identifying one of the above pays the lower band.
_LOWER_TIER = re.compile(
    r"\b(" + "|".join(sorted((re.escape(g) for g in LOWER_RATE_MARKETS), key=len, reverse=True)) + r")\b",
    re.I,
)

# A region string that means "open to everyone" still reaches paying markets.
_OPEN_TO_ALL = re.compile(r"\b(worldwide|global|anywhere|remote)\b", re.I)

# Job boards give regions rather than countries — "Americas, Europe, Israel" —
# so a bare country list wouldn't match. Anything naming a place at all, and not
# naming a lower-rate market, is treated as high tier. Two-letter codes are
# listed explicitly: requiring 3+ letters would drop "US", "UK" and "UAE".
_SHORT_CODES = r"US|UK|UAE|EU|NZ|CA|AU|DE|FR|NL|IE|CH|SE|NO|DK|FI|JP|KR|SG|HK|IL|AE|QA|ZA|BR|MX"
_NAMES_A_PLACE = re.compile(rf"[A-Za-z]{{3,}}|\b({_SHORT_CODES})\b")

GEOGRAPHY_MULTIPLIER = {
    "high": 1.0,
    "other": 0.6,
}


def high_tier_geography(client_geography: str) -> bool:
    """True when the client's market pays above Indian rates — i.e. almost
    anywhere that isn't on the exception list."""
    text = client_geography or ""
    if _LOWER_TIER.search(text):
        return False
    if _OPEN_TO_ALL.search(text):
        return True
    # A place has to actually be named. Blank or a bare postcode stays on the
    # conservative band rather than being guessed upward.
    return bool(_NAMES_A_PLACE.search(text))


def _tier_for(client_geography: str) -> str:
    return "high" if high_tier_geography(client_geography) else "other"


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
