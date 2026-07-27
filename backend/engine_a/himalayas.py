"""Himalayas — free, no auth, ~96k jobs.

Same structured-field advantage as Remotive (`employmentType` means the
contract filter is exact, not a regex guess), plus `locationRestrictions` and
salary — over a far larger corpus.

The tradeoff is density: only ~5-9% of listings are contract-shaped and the API
returns 20 per request whatever limit is asked, so it must paginate. It's a
free service, so `max_pages` is deliberately conservative rather than
exhaustive.
"""

import html
import re

import httpx

API = "https://himalayas.app/jobs/api?limit={limit}&offset={offset}"
PAGE_SIZE = 20
DEFAULT_MAX_PAGES = 5

CONTRACT_TYPES = {"Contractor", "Part Time", "Temporary"}
_TAG = re.compile(r"<[^>]+>")


def _default_http(url: str) -> dict:
    return httpx.get(url, timeout=30, headers={"User-Agent": "FreelancingAgent/1.0"}).json()


def _clean(text: str) -> str:
    return html.unescape(_TAG.sub(" ", text or "")).strip()


def _budget(j: dict) -> str | None:
    lo, hi = j.get("minSalary"), j.get("maxSalary")
    if lo is None and hi is None:
        return None
    cur = j.get("currency") or ""
    period = j.get("salaryPeriod") or ""
    span = f"{lo:g}-{hi:g}" if hi is not None else f"{lo:g}+"
    return " ".join(x for x in (cur, span, period) if x)


def fetch_himalayas(http=_default_http, max_pages: int = DEFAULT_MAX_PAGES) -> list[dict]:
    out = []
    for page in range(max_pages):
        jobs = http(API.format(limit=PAGE_SIZE, offset=page * PAGE_SIZE)).get("jobs", [])
        if not jobs:
            break
        for j in jobs:
            if j.get("employmentType") not in CONTRACT_TYPES:
                continue
            # An unrestricted remote role is open to US/EU clients; calling it
            # "" would push it into the geography-unknown pricing path.
            regions = j.get("locationRestrictions") or []
            out.append(
                {
                    "source": "himalayas",
                    "title": j.get("title", ""),
                    "description": _clean(j.get("description") or j.get("excerpt") or ""),
                    "url": j.get("applicationLink"),
                    "budget": _budget(j),
                    "location": ", ".join(regions) if regions else "Worldwide",
                }
            )
    return out
