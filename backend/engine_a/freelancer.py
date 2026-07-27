"""Freelancer.com active-projects API — free, no auth on the READ endpoint.

The project's research doc said this required OAuth + application review; that
applies to the bidding/write API. Reading live projects needs no credentials
(verified 200).

Strongest source available: `budget.minimum/maximum` and `currency.code` are
structured, so "USD/GBP/EUR work above $X" is an exact filter, not a regex
guess. Both filters are load-bearing — unfiltered, the feed is dominated by
INR low-budget listings, exactly the work this project exists to avoid.
"""

import httpx

API = (
    "https://www.freelancer.com/api/projects/0.1/projects/active/"
    "?limit={limit}&min_avg_price={min_budget}&job_details=true&full_description=true"
)

# Manan's targeting priority: dollar/pound/euro clients.
HIGH_VALUE_CURRENCIES = {"USD", "GBP", "EUR", "CAD", "AUD", "CHF", "NZD", "SGD"}

# The API's min_avg_price applies the same number to hourly and fixed projects,
# so a live pull returned "USD 2-8" and "USD 15-25" (hourly RATES) next to
# "EUR 750-1500" (a project budget). Judged on one scale either the junk gets
# through or real fixed-price work gets dropped, so they get separate floors.
# These are worth-an-LLM-call thresholds, not Manan's asking rate — his own
# pricing module puts him at $40-95/hr, but a negotiable lead below that is
# still worth seeing.
DEFAULT_MIN_HOURLY = 25
DEFAULT_MIN_FIXED = 500


def _default_http(url: str) -> dict:
    return httpx.get(url, timeout=30, headers={"User-Agent": "FreelancingAgent/1.0"}).json()


def _budget(p: dict) -> str | None:
    b = p.get("budget") or {}
    lo, hi = b.get("minimum"), b.get("maximum")
    if lo is None and hi is None:
        return None
    code = (p.get("currency") or {}).get("code", "")
    return f"{code} {lo:g}-{hi:g}" if hi is not None else f"{code} {lo:g}+"


def _budget_ok(p: dict, min_hourly: int, min_fixed: int) -> bool:
    lo = (p.get("budget") or {}).get("minimum")
    if lo is None:
        return True  # no budget stated — let the scorer judge it
    floor = min_hourly if p.get("type") == "hourly" else min_fixed
    return lo >= floor


def fetch_freelancer(
    http=_default_http,
    min_budget: int = DEFAULT_MIN_FIXED,
    limit: int = 50,
    min_hourly: int = DEFAULT_MIN_HOURLY,
    min_fixed: int = DEFAULT_MIN_FIXED,
) -> list[dict]:
    url = API.format(limit=limit, min_budget=min_budget)
    out = []
    for p in http(url).get("result", {}).get("projects", []):
        if (p.get("currency") or {}).get("code") not in HIGH_VALUE_CURRENCIES:
            continue
        if not _budget_ok(p, min_hourly, min_fixed):
            continue
        # Skills carry the tech signal the title often lacks, and the matcher
        # embeds the description — so append them rather than dropping them.
        skills = ", ".join(j.get("name", "") for j in (p.get("jobs") or []) if j.get("name"))
        body = p.get("description") or p.get("preview_description") or ""
        seo = p.get("seo_url")
        out.append(
            {
                "source": "freelancer",
                "title": p.get("title", ""),
                "description": f"{body}\n\nSkills: {skills}" if skills else body,
                "url": f"https://www.freelancer.com/projects/{seo}" if seo else None,
                "budget": _budget(p),
                # Currency is not a country — leave location empty rather than
                # inventing one from it.
                "location": ((p.get("location") or {}).get("country") or {}).get("name") or "",
            }
        )
    return out
