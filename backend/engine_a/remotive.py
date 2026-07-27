"""Remotive — free, no auth, and the only board here exposing a structured
`job_type`, so its freelance filter is exact rather than a regex guess.

Also carries `candidate_required_location` and `salary`, which matter for
targeting USD/GBP/EUR clients: a live pull surfaced "Senior Independent AI
Engineer / Architect, Americas+Europe, $120-$170/hour".
"""

import html
import re

import httpx

API = "https://remotive.com/api/remote-jobs?limit=200"
FREELANCE_TYPES = {"contract", "freelance"}
_TAG = re.compile(r"<[^>]+>")


def _default_http(url: str) -> dict:
    return httpx.get(url, timeout=30, headers={"User-Agent": "FreelancingAgent/1.0"}).json()


def _clean(text: str) -> str:
    return html.unescape(_TAG.sub(" ", text or "")).strip()


def fetch_remotive(http=_default_http) -> list[dict]:
    out = []
    for j in http(API).get("jobs", []):
        if (j.get("job_type") or "").lower() not in FREELANCE_TYPES:
            continue
        out.append(
            {
                "source": "remotive",
                "title": j.get("title", ""),
                "description": _clean(j.get("description", "")),
                "url": j.get("url"),
                "budget": j.get("salary") or None,
                "location": j.get("candidate_required_location", ""),
            }
        )
    return out
