"""Working Nomads — free, no auth. Carries a location but no engagement field,
so the shared freelance filter in sources.py does the screening.
"""

import html
import re

import httpx

API = "https://www.workingnomads.com/api/exposed_jobs/"
_TAG = re.compile(r"<[^>]+>")


def _default_http(url: str) -> list:
    return httpx.get(url, timeout=30, headers={"User-Agent": "FreelancingAgent/1.0"}).json()


def _clean(text: str) -> str:
    return html.unescape(_TAG.sub(" ", text or "")).strip()


def fetch_working_nomads(http=_default_http) -> list[dict]:
    return [
        {
            "source": "workingnomads",
            "title": j.get("title", ""),
            "description": _clean(j.get("description", "")),
            "url": j.get("url"),
            "budget": None,
            "location": j.get("location", ""),
        }
        for j in http(API)
    ]
