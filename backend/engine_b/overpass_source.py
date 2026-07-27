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

MIRRORS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.osm.jp/api/interpreter",
]

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
        for mirror in MIRRORS:
            try:
                data = post(mirror, query)
                break
            except Exception:
                log.warning("overpass mirror %s failed for %s; trying next", mirror, area)
        if data is None:
            log.error("all overpass mirrors failed for %s; skipping", area)
            continue
        for el in data.get("elements", []):
            target = _to_target(el, area)
            if target:
                out.append(target)
    return out
