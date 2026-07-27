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
