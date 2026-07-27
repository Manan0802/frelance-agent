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

from backend.engine_b.overpass_source import fetch_overpass, MIRRORS, CATEGORIES


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
    """The main endpoint 504s under load; a dead mirror must not cost the run."""
    post, calls = _post(RuntimeError("504 timeout"), {"elements": [_element()]})
    rows = fetch_overpass([("Austin", (0, 0, 1, 1))], post=post, spacing=0)
    assert len(rows) == 1
    assert calls["urls"][0] != calls["urls"][1], "second attempt used a different mirror"


def test_area_is_skipped_when_every_mirror_fails():
    post, _ = _post(*[RuntimeError("down")] * (len(MIRRORS) + 2))
    rows = fetch_overpass([("Austin", (0, 0, 1, 1)), ("London", (0, 0, 1, 1))],
                          post=post, spacing=0)
    assert rows == []


def test_query_targets_the_requested_bbox_and_categories():
    post, calls = _post({"elements": []})
    fetch_overpass([("Austin", (30.2, -97.8, 30.3, -97.6))],
                   categories=["dentist"], post=post, spacing=0)
    body = calls["bodies"][0]
    assert "30.2,-97.8,30.3,-97.6" in body
    assert "dentist" in body


def test_each_area_is_queried():
    post, calls = _post({"elements": []}, {"elements": []})
    fetch_overpass([("Austin", (0, 0, 1, 1)), ("London", (2, 2, 3, 3))], post=post, spacing=0)
    assert calls["n"] == 2


def test_default_categories_are_the_high_value_service_businesses():
    """Chosen for margin + manual workload: clinics, professional offices.
    Deliberately not restaurants/retail — low margin, already aggregator-served."""
    assert "dentist" in CATEGORIES
    assert "restaurant" not in CATEGORIES
