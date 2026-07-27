"""Prebuilt target areas, so Engine B can reach volume without hand-writing
bounding boxes.

Manan's stated priority is USD/GBP/EUR clients — "two dollar clients beat a run
of INR work" — so the default set is US/UK/EU cities. Delhi stays available for
local work, but is not the default.
"""

from backend.engine_b.areas import AREAS, DEFAULT_AREAS, areas_for
from backend.pricing.suggest import high_tier_geography


def test_default_areas_are_high_currency():
    for label, _bbox in DEFAULT_AREAS:
        assert high_tier_geography(label), f"{label} is not a high-currency market"


def test_bboxes_are_ordered_south_west_north_east():
    """Overpass rejects a bbox given in the wrong order, and it fails as a
    timeout rather than an obvious error — worth asserting."""
    for label, (south, west, north, east) in AREAS.items():
        assert south < north, f"{label}: south must be below north"
        assert west < east, f"{label}: west must be left of east"


def test_bboxes_are_plausible_coordinates():
    for label, (south, west, north, east) in AREAS.items():
        assert -90 <= south < north <= 90, label
        assert -180 <= west < east <= 180, label


def test_areas_are_small_enough_to_query():
    """A whole-country box times Overpass out. City-sized means roughly a
    degree or less on each side."""
    for label, (south, west, north, east) in AREAS.items():
        assert north - south <= 1.0, f"{label} spans too much latitude"
        assert east - west <= 1.5, f"{label} spans too much longitude"


def test_areas_for_selects_by_name():
    picked = areas_for(["Austin", "London"])
    assert [label for label, _ in picked] == ["Austin, USA", "London, UK"]


def test_areas_for_is_case_insensitive_and_ignores_unknown_names():
    assert [l for l, _ in areas_for(["austin", "nowhere-city"])] == ["Austin, USA"]


def test_areas_for_returns_defaults_when_asked_for_nothing():
    assert areas_for([]) == DEFAULT_AREAS


def test_delhi_is_available_but_not_a_default():
    assert any("Delhi" in label for label in AREAS)
    assert not any("Delhi" in label for label, _ in DEFAULT_AREAS)


def test_india_is_covered_properly_not_just_delhi():
    """Manan: "overseas, India, sab jagah" — both markets, not one token city."""
    india = [l for l in AREAS if l.endswith("India")]
    assert len(india) >= 6, f"only {len(india)} Indian cities"
    for city in ("Mumbai", "Bengaluru", "Pune", "Hyderabad"):
        assert any(city in l for l in AREAS), f"{city} missing"


def test_major_english_speaking_and_eu_markets_are_covered():
    for city in ("New York", "San Francisco", "Chicago", "Dublin", "Singapore", "Dubai"):
        assert any(city in l for l in AREAS), f"{city} missing"


def test_areas_can_be_selected_by_country():
    from backend.engine_b.areas import areas_for

    indian = areas_for(["India"])
    assert len(indian) >= 6
    assert all(l.endswith("India") for l, _ in indian)


def test_country_and_city_selection_can_be_mixed():
    from backend.engine_b.areas import areas_for

    picked = [l for l, _ in areas_for(["India", "London"])]
    assert any(l.endswith("India") for l in picked)
    assert "London, UK" in picked
