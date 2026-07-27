"""Global city coverage for Engine B.

Manan's scope is every continent — "North America, Europe, Australia, Asia,
South America, Africa... itni saari countries hai". So cities are stored as a
centre point and the bbox is derived, rather than four hand-written numbers per
city: hundreds of entries stay reviewable, and a typo in one coordinate can't
silently produce an inverted or planet-sized box.

Defaults stay USD/GBP/EUR because two dollar-paying clients are worth a run of
INR work, but any city or whole country is one argument away.
"""

from backend.engine_b.areas import (
    AREAS, CITIES, DEFAULT_AREAS, areas_for, bbox_for, COUNTRIES,
)
from backend.pricing.suggest import high_tier_geography


def test_default_areas_are_high_currency():
    for label, _bbox in DEFAULT_AREAS:
        assert high_tier_geography(label), f"{label} is not a high-currency market"


def test_bboxes_are_ordered_south_west_north_east():
    """Overpass rejects a reversed bbox as a timeout rather than a clear error."""
    for label, (south, west, north, east) in AREAS.items():
        assert south < north, f"{label}: south must be below north"
        assert west < east, f"{label}: west must be left of east"


def test_coordinates_are_plausible():
    for label, (lat, lon) in CITIES.items():
        assert -90 <= lat <= 90, f"{label}: latitude out of range"
        assert -180 <= lon <= 180, f"{label}: longitude out of range"
        assert (lat, lon) != (0.0, 0.0), f"{label}: null island — missing coordinates"


def test_areas_stay_city_sized():
    """A country-scale box times Overpass out."""
    for label, (south, west, north, east) in AREAS.items():
        assert north - south <= 0.5, f"{label} spans too much latitude"
        assert east - west <= 1.0, f"{label} spans too much longitude"


def test_longitude_span_widens_near_the_poles():
    """A degree of longitude shrinks with latitude, so a fixed degree box would
    cover far less ground in Stockholm than in Singapore."""
    _, w_trop, _, e_trop = bbox_for(1.29, 103.85)      # Singapore
    _, w_nordic, _, e_nordic = bbox_for(59.33, 18.06)  # Stockholm
    assert (e_nordic - w_nordic) > (e_trop - w_trop)


def test_every_continent_is_covered():
    for country in ("USA", "UK", "Germany", "India", "Australia", "Brazil",
                    "South Africa", "Japan", "Mexico", "Nigeria"):
        assert any(l.endswith(country) for l in CITIES), f"{country} missing"


def test_coverage_is_actually_global_in_scale():
    assert len(CITIES) >= 180, f"only {len(CITIES)} cities"
    assert len(COUNTRIES) >= 40, f"only {len(COUNTRIES)} countries"


def test_india_is_covered_in_depth():
    india = [l for l in CITIES if l.endswith("India")]
    assert len(india) >= 15, f"only {len(india)} Indian cities"
    for city in ("Mumbai", "Bengaluru", "Pune", "Hyderabad", "Jaipur", "Indore"):
        assert any(city in l for l in CITIES), f"{city} missing"


def test_areas_can_be_selected_by_country():
    indian = areas_for(["India"])
    assert len(indian) >= 15
    assert all(l.endswith("India") for l, _ in indian)


def test_country_and_city_selection_can_be_mixed():
    picked = [l for l, _ in areas_for(["India", "London"])]
    assert any(l.endswith("India") for l in picked)
    assert "London, UK" in picked


def test_selection_is_case_insensitive_and_ignores_unknown_names():
    assert [l for l, _ in areas_for(["austin", "nowhere-city"])] == ["Austin, USA"]


def test_areas_for_returns_defaults_when_asked_for_nothing():
    assert areas_for([]) == DEFAULT_AREAS


def test_city_labels_are_unique_and_well_formed():
    for label in CITIES:
        assert ", " in label, f"{label} should read 'City, Country'"
