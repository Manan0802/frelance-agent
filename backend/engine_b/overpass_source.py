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

# Scope is every kind of business, small to large — solo tradespeople through
# startups, corporates and factories — because the offer is software/AI/
# automation for whatever they currently do by hand, not one vertical's website.
#
# Split by OSM tag family, and queried as separate requests: a single query
# across all of this reliably 504s on a load-flaky endpoint, and one failure
# would cost the whole city. Per-family means small requests and partial
# failures.
TAG_FAMILIES: dict[str, list[str]] = {
    # Appointment- and intake-heavy services
    "amenity": [
        "dentist", "doctors", "clinic", "veterinary", "pharmacy", "nursing_home",
        "driving_school", "language_school", "prep_school", "music_school",
        "childcare", "kindergarten", "college", "training",
        "bank", "car_rental", "car_wash", "coworking_space", "funeral_hall",
        "events_venue", "conference_centre", "studio",
    ],
    # Professional services, companies, startups
    "office": [
        "lawyer", "accountant", "tax_advisor", "notary", "estate_agent",
        "insurance", "financial", "financial_advisor", "property_management",
        "architect", "engineer", "surveyor", "logistics", "moving_company",
        "employment_agency", "recruitment", "educational_institution",
        "company", "it", "consulting", "research", "telecommunication",
        "advertising_agency", "marketing", "newspaper", "publisher",
        "travel_agent", "security", "energy_supplier", "water_utility",
    ],
    # Trades — heavy manual scheduling, quoting and job tracking
    "craft": [
        "electrician", "plumber", "carpenter", "hvac", "roofer", "painter",
        "builder", "joiner", "gardener", "locksmith", "glaziery", "tiler",
        "metal_construction", "blacksmith", "sawmill", "caterer", "photographer",
        "signmaker", "upholsterer", "window_construction", "brewery", "winery",
        "confectionery", "electronics_repair", "handicraft",
    ],
    # Clinical practices beyond the amenity tag
    "healthcare": [
        "physiotherapist", "psychotherapist", "optometrist", "podiatrist",
        "speech_therapist", "occupational_therapist", "dietitian", "midwife",
        "alternative", "laboratory", "sample_collection", "rehabilitation",
    ],
    # Retail and repair — stock, bookings, quotes
    "shop": [
        "car", "car_repair", "car_parts", "motorcycle", "bicycle", "tyres",
        "furniture", "kitchen", "bathroom_furnishing", "doityourself",
        "hardware", "trade", "building_materials", "flooring", "windows",
        "optician", "hearing_aids", "medical_supply", "herbalist",
        "jewelry", "watches", "shoe_repair", "tailor", "dry_cleaning", "laundry",
        "beauty", "hairdresser", "massage", "nutrition_supplements",
        "printing", "copyshop", "photo", "funeral_directors",
        "travel_agency", "estate_agent", "wholesale", "garden_centre",
        "storage_rental", "party", "pet_grooming",
    ],
    # Hospitality — booking and enquiry automation
    "tourism": ["hotel", "guest_house", "hostel", "motel", "apartment", "chalet"],
    # Studios, gyms, clubs — memberships and class scheduling
    "leisure": ["fitness_centre", "sports_centre", "dance", "golf_course", "horse_riding"],
}

# Industry is tagged as landuse/building rather than as a business category, and
# appears as ways more often than nodes.
INDUSTRIAL_CATEGORIES = ["industrial", "factory", "warehouse", "wholesale", "commercial"]

# Kept for callers that passed these explicitly.
CATEGORIES = TAG_FAMILIES["amenity"]
OFFICE_CATEGORIES = TAG_FAMILIES["office"]

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


def _family_query(bbox, tag: str, values: list[str], limit: int) -> str:
    box = ",".join(str(c) for c in bbox)
    clause = f'  nwr["{tag}"~"^({"|".join(values)})$"]["name"]({box});'
    return QUERY.format(clauses=clause, limit=limit)


def _industrial_query(bbox, values: list[str], limit: int) -> str:
    box = ",".join(str(c) for c in bbox)
    alt = "|".join(values)
    clauses = (
        f'  nwr["landuse"~"^({alt})$"]["name"]({box});\n'
        f'  nwr["building"~"^({alt})$"]["name"]({box});'
    )
    return QUERY.format(clauses=clauses, limit=limit)


def _queries_for(bbox, families: dict, industrial: list[str], limit: int) -> list[str]:
    out = [_family_query(bbox, tag, vals, limit) for tag, vals in families.items() if vals]
    if industrial:
        out.append(_industrial_query(bbox, industrial, limit))
    return out


def _address(tags: dict) -> str:
    street = " ".join(x for x in (tags.get("addr:housenumber"), tags.get("addr:street")) if x)
    parts = [street, tags.get("addr:city"), tags.get("addr:postcode")]
    return ", ".join(p for p in parts if p)


# Values that classify nothing. `building=yes` merely means "a building", and a
# live run produced 50 rows carrying it — "a yes in Austin" reads worse in a
# pitch than saying nothing at all.
_EMPTY_CATEGORY_VALUES = {"yes", "true", "commercial", "retail", "office"}


def _category(tags: dict) -> str | None:
    """Read the category from whichever family matched. Every tag family in the
    query needs to be here: a live run left 238 of 658 businesses with category
    None because the newer families were queried but never read back, and the
    writer prompt uses this ("a {category} in {location}")."""
    for tag in ("amenity", "office", "craft", "healthcare", "shop",
                "tourism", "leisure", "landuse", "building"):
        value = tags.get(tag)
        if value and value.lower() not in _EMPTY_CATEGORY_VALUES:
            return value
    return None


def _to_target(el: dict, area: str) -> dict | None:
    tags = el.get("tags") or {}
    name = tags.get("name")
    if not name:
        return None  # an unnamed node can't be identified, let alone pitched
    # A branded chain/corporate location isn't a freelance client — decisions
    # happen at HQ, not the branch — and OSM often omits their website tag, so
    # the no-website angle would tell Google "I couldn't find your site".
    # Verified on live Austin data: brand:wikidata was set on Google, Meta,
    # McKinsey, Accenture and Cloudflare, and on 1 of 31 small local firms.
    if tags.get("brand") or tags.get("brand:wikidata"):
        return None
    # Querying industrial land returns electricity substations, power plants,
    # water treatment works and municipal depots — infrastructure, not
    # businesses that buy software. A live Austin sample was over half these.
    if tags.get("power") or tags.get("man_made"):
        return None
    return {
        "name": name,
        "address": _address(tags) or area,
        "website": tags.get("website") or tags.get("contact:website") or None,
        "phone": tags.get("phone") or tags.get("contact:phone") or None,
        "email": tags.get("email") or tags.get("contact:email") or None,
        "category": _category(tags),
    }


def _fetch_one(query: str, area: str, post, retry_delay: float) -> dict | None:
    for attempt in range(MAX_ATTEMPTS):
        mirror = MIRRORS[attempt % len(MIRRORS)]
        try:
            return post(mirror, query)
        except Exception:
            log.warning("overpass %s failed for %s (attempt %d)", mirror, area, attempt + 1)
            # The same endpoint can succeed moments later, so wait before
            # coming back round to it.
            if retry_delay and attempt >= len(MIRRORS) - 1:
                time.sleep(retry_delay)
    return None


def fetch_overpass(
    areas,
    families=None,
    industrial_categories=None,
    post=_default_post,
    spacing: float = REQUEST_SPACING_SECONDS,
    limit: int = MAX_PER_AREA,
    retry_delay: float = RETRY_DELAY_SECONDS,
) -> list[dict]:
    """areas: [(label, (south, west, north, east)), ...]

    One request per tag family: a single query across every category reliably
    504s, and a failure would cost the whole city rather than one slice.
    """
    fams = TAG_FAMILIES if families is None else families
    industrial = INDUSTRIAL_CATEGORIES if industrial_categories is None else industrial_categories

    out: list[dict] = []
    seen: set[tuple] = set()
    for area, bbox in areas:
        for i, query in enumerate(_queries_for(bbox, fams, industrial, limit)):
            if (i or out) and spacing:
                time.sleep(spacing)
            data = _fetch_one(query, area, post, retry_delay)
            if data is None:
                log.error("overpass: all attempts failed for %s (one family); skipping", area)
                continue
            for el in data.get("elements", []):
                target = _to_target(el, area)
                if not target:
                    continue
                # A business can carry tags matched by two families; don't
                # pitch it twice.
                key = (target["name"].lower(), target["address"].lower())
                if key in seen:
                    continue
                seen.add(key)
                out.append(target)
    return out
