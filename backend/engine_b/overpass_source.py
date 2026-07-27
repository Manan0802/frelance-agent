"""OpenStreetMap Overpass — Engine B's volume source. Free, no auth, no key,
no Docker, global.

Measured live: one Austin bbox across dentists/lawyers/accountants/estate
agents returned 76 named businesses, 35 with no website at all. The
no-website half is the *best* segment, not waste — "I searched and couldn't
find your site" is a verified fact and that pitch scores 8/10 (Phase 7).

What it does NOT give: reliable contact details. On the no-website rows,
phone coverage was 0/37 in the live sample. Overpass gives reach and
qualification; contact enrichment is a separate problem.

Built around two observed realities: the main endpoint 504s under repeated
querying (and kumi.systems timed out entirely) while private.coffee answered
200, so mirrors are tried in turn; and it's a donated free service, so area
queries are spaced.
"""

import logging
import time

import httpx

# Measured 2026-07-27 with an identical light query:
#   overpass-api.de      200 in ~2s
#   private.coffee       ReadTimeout at 40s
#   kumi.systems         ReadTimeout at 40s
#   maps.mail.ru         504
#   overpass.osm.ch      200 but 0 elements (regional instance — useless here)
#   overpass.osm.jp      ConnectError, SSL hostname mismatch (broken)
# Verified-working first; the two timeouts stay as fallbacks since load shifts.
MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# The public endpoint is load-flaky rather than query-flaky: measured live, one
# query 504'd while a strictly heavier one succeeded seconds later. So failures
# are retried, not just routed around once.
MAX_ATTEMPTS = 6
RETRY_DELAY_SECONDS = 5

# Chosen for margin + manual workload: appointment-booking and document-heavy
# service businesses. Deliberately excludes restaurants/retail — low margin and
# already served by aggregators.
CATEGORIES = ["dentist", "doctors", "clinic", "veterinary", "driving_school"]
OFFICE_CATEGORIES = ["lawyer", "accountant", "estate_agent", "insurance", "financial"]

REQUEST_SPACING_SECONDS = 3
MAX_PER_AREA = 200

QUERY = """[out:json][timeout:60];
(
{clauses}
);
out body {limit};
"""

log = logging.getLogger(__name__)


def _default_post(url: str, query: str) -> dict:
    r = httpx.post(url, content=query.encode(), timeout=90,
                   headers={"User-Agent": "FreelancingAgent/1.0"})
    r.raise_for_status()
    return r.json()


def _build_query(bbox, categories, office_categories, limit) -> str:
    box = ",".join(str(c) for c in bbox)
    clauses = [f'  node["amenity"="{c}"]({box});' for c in categories]
    if office_categories:
        clauses.append(f'  node["office"~"{"|".join(office_categories)}"]({box});')
    return QUERY.format(clauses="\n".join(clauses), limit=limit)


def _address(tags: dict) -> str:
    street = " ".join(x for x in (tags.get("addr:housenumber"), tags.get("addr:street")) if x)
    parts = [street, tags.get("addr:city"), tags.get("addr:postcode")]
    return ", ".join(p for p in parts if p)


def _to_target(el: dict, area: str) -> dict | None:
    tags = el.get("tags") or {}
    name = tags.get("name")
    if not name:
        return None  # an unnamed node can't be identified, let alone pitched
    return {
        "name": name,
        "address": _address(tags) or area,
        "website": tags.get("website") or tags.get("contact:website") or None,
        "phone": tags.get("phone") or tags.get("contact:phone") or None,
        "email": tags.get("email") or tags.get("contact:email") or None,
        "category": tags.get("amenity") or tags.get("office"),
    }


def fetch_overpass(
    areas,
    categories=None,
    office_categories=None,
    post=_default_post,
    spacing: float = REQUEST_SPACING_SECONDS,
    limit: int = MAX_PER_AREA,
    retry_delay: float = RETRY_DELAY_SECONDS,
) -> list[dict]:
    """areas: [(label, (south, west, north, east)), ...]"""
    cats = CATEGORIES if categories is None else categories
    offices = OFFICE_CATEGORIES if office_categories is None else office_categories

    out = []
    for i, (area, bbox) in enumerate(areas):
        if i and spacing:
            time.sleep(spacing)
        query = _build_query(bbox, cats, offices, limit)
        data = None
        for attempt in range(MAX_ATTEMPTS):
            mirror = MIRRORS[attempt % len(MIRRORS)]
            try:
                data = post(mirror, query)
                break
            except Exception:
                log.warning("overpass %s failed for %s (attempt %d)", mirror, area, attempt + 1)
                # Same endpoint can succeed moments later, so wait before
                # coming back round to it.
                if retry_delay and attempt >= len(MIRRORS) - 1:
                    time.sleep(retry_delay)
        if data is None:
            log.error("overpass: all attempts failed for %s; skipping", area)
            continue
        for el in data.get("elements", []):
            target = _to_target(el, area)
            if target:
                out.append(target)
    return out
