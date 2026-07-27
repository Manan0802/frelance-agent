"""Hacker News "Ask HN: Freelancer? Seeking freelancer?" — the monthly thread.

Free, no auth. Two conventions run in that thread: "SEEKING WORK" (freelancers
advertising — competitors) and "SEEKING FREELANCER" (clients hiring — leads).

Measured Apr-Jul 2026: ~87 top-level comments, exactly ONE was SEEKING
FREELANCER. Volume here is roughly one lead a month, so treat it as a
low-volume/high-quality trickle, not a pipeline. The filter matters more than
the fetch: without it this feeds ~85 competitor ads into the scorer.
"""

import html
import re

import httpx

SEARCH_URL = (
    "https://hn.algolia.com/api/v1/search_by_date"
    "?query=freelancer%20seeking%20freelancer&tags=story&hitsPerPage=3"
)
ITEM_URL = "https://hn.algolia.com/api/v1/items/{id}"

# The thread title is always "Ask HN: Freelancer? Seeking freelancer? (Month Year)".
_THREAD_TITLE = re.compile(r"freelancer\?\s*seeking freelancer\?", re.I)
_MARKER = re.compile(r"seeking\s+freelancer", re.I)
_TAG = re.compile(r"<[^>]+>")
# Only the opening of a comment declares its side; a SEEKING WORK ad may mention
# the other phrase further down.
_HEAD_CHARS = 120


def _default_get(url: str) -> dict:
    return httpx.get(url, timeout=20, headers={"User-Agent": "FreelancingAgent/1.0"}).json()


def _clean(text: str) -> str:
    return html.unescape(_TAG.sub(" ", text)).strip()


def _is_seeking_freelancer(text: str) -> bool:
    return bool(_MARKER.search(_clean(text)[:_HEAD_CHARS]))


def fetch_hn_freelance(search=_default_get, item=_default_get) -> list[dict]:
    threads = [
        h for h in search(SEARCH_URL).get("hits", [])
        if _THREAD_TITLE.search(h.get("title") or "")
    ]
    out = []
    for t in threads:
        for c in item(ITEM_URL.format(id=t["objectID"])).get("children", []):
            text = c.get("text")
            if not text or not _is_seeking_freelancer(text):
                continue
            body = _clean(text)
            out.append(
                {
                    "source": "hn_freelance",
                    "title": body[:100],
                    "description": body,
                    "url": f"https://news.ycombinator.com/item?id={c['id']}",
                    "budget": None,
                }
            )
    return out
