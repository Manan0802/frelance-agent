"""OpenStreetMap Overpass — free, no auth, no key, no Docker, global.

This is the volume answer for Engine B. One Austin bbox across dentists,
lawyers, accountants and estate agents returned 76 named businesses live, 35 of
them with no website at all — and "no website" is the segment that scores 8/10,
because the absence is a verified fact rather than an inference (Phase 7).

Two operational realities it must be built around, both observed:
- The main endpoint returns 504 under repeated querying, and
  overpass.kumi.systems timed out entirely, while overpass.private.coffee
  answered 200. So: try mirrors in turn.
- It's a free, donated service. Sleep between area queries; don't hammer it.
"""

from backend.engine_b.overpass_source import (
    fetch_overpass, MIRRORS, CATEGORIES, MAX_ATTEMPTS,
)


def _element(**tags):
    base = {"lat": 30.2, "lon": -97.7, "tags": {"name": "Austin Dental", "amenity": "dentist"}}
    base["tags"].update(tags)
    return base


def _post(*responses):
    calls = {"n": 0, "urls": [], "bodies": []}

    def post(url, query):
        i = calls["n"]
        calls["n"] += 1
        calls["urls"].append(url)
        calls["bodies"].append(query)
        r = responses[i] if i < len(responses) else {"elements": []}
        if isinstance(r, Exception):
            raise r
        return r
    return post, calls


def test_maps_osm_tags_to_engine_b_target_shape():
    post, _ = _post({"elements": [_element(
        **{"name": "High Point Dentistry", "phone": "+1 512 555 0100",
           "website": "https://example.com", "addr:street": "5th St",
           "addr:city": "Austin", "addr:housenumber": "12"})]})

    rows = fetch_overpass([("Austin", (30.2, -97.8, 30.3, -97.6))], post=post, spacing=0)

    r = rows[0]
    assert r["name"] == "High Point Dentistry"
    assert r["website"] == "https://example.com"
    assert r["phone"] == "+1 512 555 0100"
    assert r["category"] == "dentist"
    assert "12 5th St" in r["address"] and "Austin" in r["address"]


def test_businesses_without_a_website_are_kept_they_are_the_best_segment():
    """The no-website half is the strongest pitch angle, not a defect."""
    post, _ = _post({"elements": [_element(name="No Site Dental")]})
    rows = fetch_overpass([("Austin", (0, 0, 1, 1))], post=post, spacing=0)
    assert rows[0]["website"] is None


def test_unnamed_elements_are_dropped():
    """An OSM node with no name can't be pitched or even identified."""
    post, _ = _post({"elements": [_element(), {"lat": 1, "lon": 1, "tags": {"amenity": "dentist"}}]})
    rows = fetch_overpass([("Austin", (0, 0, 1, 1))], post=post, spacing=0)
    assert len(rows) == 1


def test_contact_prefixed_tags_are_read_too():
    """OSM has two conventions for the same fact."""
    post, _ = _post({"elements": [_element(
        **{"contact:website": "https://x.com", "contact:phone": "555"})]})
    rows = fetch_overpass([("Austin", (0, 0, 1, 1))], post=post, spacing=0)
    assert rows[0]["website"] == "https://x.com"
    assert rows[0]["phone"] == "555"


def test_falls_over_to_the_next_mirror_when_one_fails():
    post, calls = _post(RuntimeError("504 timeout"), {"elements": [_element()]})
    rows = fetch_overpass([("Austin", (0, 0, 1, 1))], post=post, spacing=0)
    assert len(rows) == 1
    assert calls["urls"][0] != calls["urls"][1], "second attempt used a different mirror"


def test_retries_after_exhausting_the_mirrors():
    """Measured live: the SAME endpoint 504s on one query and succeeds on a
    heavier one seconds later — it's load-dependent, not query-dependent. So a
    failure is worth retrying, not just routing around once."""
    post, calls = _post(*([RuntimeError("504")] * len(MIRRORS) + [{"elements": [_element()]}]))
    rows = fetch_overpass([("Austin", (0, 0, 1, 1))], families={"amenity": ["dentist"]},
                          industrial_categories=[], post=post, spacing=0, retry_delay=0)
    assert len(rows) == 1
    assert calls["n"] == len(MIRRORS) + 1, "came back round to a mirror it had already tried"


def test_area_is_skipped_when_everything_fails():
    post, calls = _post(*[RuntimeError("down")] * 200)
    rows = fetch_overpass([("Austin", (0, 0, 1, 1)), ("London", (0, 0, 1, 1))],
                          families={"amenity": ["dentist"]}, industrial_categories=[],
                          post=post, spacing=0, retry_delay=0)
    assert rows == []
    assert calls["n"] == 2 * MAX_ATTEMPTS, "gives up per query rather than retrying forever"


def test_mirrors_are_ordered_with_the_verified_working_one_first():
    """Measured: overpass-api.de answered 200 in ~2s while private.coffee and
    kumi.systems both read-timed-out at 40s."""
    assert "overpass-api.de" in MIRRORS[0]


def test_query_targets_the_requested_bbox_and_categories():
    post, calls = _post({"elements": []})
    fetch_overpass([("Austin", (30.2, -97.8, 30.3, -97.6))],
                   families={"amenity": ["dentist"]}, industrial_categories=[],
                   post=post, spacing=0)
    body = calls["bodies"][0]
    assert "30.2,-97.8,30.3,-97.6" in body
    assert "dentist" in body


def test_each_area_is_queried():
    post, calls = _post(*[{"elements": []}] * 4)
    fetch_overpass([("Austin", (0, 0, 1, 1)), ("London", (2, 2, 3, 3))],
                   families={"amenity": ["dentist"]}, industrial_categories=[],
                   post=post, spacing=0)
    assert calls["n"] == 2
    assert "0,0,1,1" in calls["bodies"][0] and "2,2,3,3" in calls["bodies"][1]


def test_default_categories_are_the_high_value_service_businesses():
    """Chosen for margin + manual workload: clinics, professional offices.
    Deliberately not restaurants/retail — low margin, already aggregator-served."""
    assert "dentist" in CATEGORIES
    assert "restaurant" not in CATEGORIES


def test_targets_span_small_business_through_industry_and_corporate():
    """Manan's scope: "factory owners, business owners, startups, corporates —
    big to small". Clinics and law offices alone miss the industrial and
    company-office segments, which are where operational software and process
    automation actually sell."""
    from backend.engine_b.overpass_source import OFFICE_CATEGORIES, INDUSTRIAL_CATEGORIES

    assert {"company", "it", "consulting"} <= set(OFFICE_CATEGORIES), "corporate offices"
    assert INDUSTRIAL_CATEGORIES, "factories/warehouses must be targetable"


def test_branded_chain_and_corporate_locations_are_dropped():
    """Broadening to offices pulled in Google, Meta, McKinsey, Accenture and
    Cloudflare branch locations. They don't hire solo freelancers by cold
    email, and OSM often omits their `website` tag — so the pipeline would
    cheerfully tell Google "I searched and couldn't find your website".

    Verified against live Austin data: `brand:wikidata` was present on those
    corporates and on only 1 of 31 small local firms."""
    post, _ = _post({"elements": [
        _element(name="Google", **{"brand:wikidata": "Q95", "brand": "Google"}),
        _element(name="Local Dental Care"),
    ]})
    rows = fetch_overpass([("Austin", (0, 0, 1, 1))], post=post, spacing=0)
    assert [r["name"] for r in rows] == ["Local Dental Care"]


def test_a_plain_wikidata_tag_alone_does_not_disqualify():
    """A local firm notable enough for a Wikidata entry is still a fine target —
    live data had exactly one (Zello). It's the BRAND tag that marks a chain."""
    post, _ = _post({"elements": [_element(name="Zello", wikidata="Q123")]})
    rows = fetch_overpass([("Austin", (0, 0, 1, 1))], post=post, spacing=0)
    assert [r["name"] for r in rows] == ["Zello"]


def test_industrial_targets_are_queried_too():
    post, calls = _post(*[{"elements": []}] * 20)
    fetch_overpass([("Austin", (0, 0, 1, 1))], post=post, spacing=0)
    assert any("industrial" in b or "factory" in b for b in calls["bodies"])


def test_every_tag_family_is_queried_separately():
    """One mega-query across every category reliably 504s on a load-flaky
    endpoint, and a single failure would cost the whole city. Splitting by tag
    family keeps each request small and makes failures partial."""
    from backend.engine_b.overpass_source import TAG_FAMILIES

    post, calls = _post(*[{"elements": []}] * 30)
    fetch_overpass([("Austin", (0, 0, 1, 1))], post=post, spacing=0)
    assert calls["n"] == len(TAG_FAMILIES) + 1, "every family, plus industrial"


def test_one_failing_family_does_not_lose_the_rest():
    def post(url, query):
        if "craft" in query:
            raise RuntimeError("504")
        return {"elements": [_element(name=f"Biz {url[-1]}")]}

    rows = fetch_overpass([("Austin", (0, 0, 1, 1))], post=post, spacing=0, retry_delay=0)
    assert rows, "other families still returned results"


def test_the_same_business_is_not_returned_twice():
    """A firm can carry tags matched by two families (office=company and
    shop=... say); it must not be pitched twice."""
    dup = _element(name="Acme Ltd", **{"addr:street": "5th St"})
    post, _ = _post(*[{"elements": [dup]}] * 30)
    rows = fetch_overpass([("Austin", (0, 0, 1, 1))], post=post, spacing=0)
    assert len(rows) == 1


def test_coverage_spans_trades_health_hospitality_and_retail():
    """"Chhote se bade sabko" — solo tradespeople through to industry."""
    from backend.engine_b.overpass_source import TAG_FAMILIES

    allv = " ".join(str(v) for v in TAG_FAMILIES.values())
    for expected in ("electrician", "plumber", "physiotherapist", "hotel",
                     "hairdresser", "car_repair", "fitness_centre", "company"):
        assert expected in allv, f"{expected} missing from target coverage"
