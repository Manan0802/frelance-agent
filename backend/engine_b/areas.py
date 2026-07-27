"""Prebuilt city bounding boxes for Overpass, so reaching volume doesn't mean
hand-writing coordinates.

Defaults are USD/GBP/EUR markets, per Manan's targeting priority. Delhi is kept
available for local work but is deliberately not a default.

Boxes are city-centre sized: Overpass times out on anything country-scale, and
it fails as a timeout rather than a clear error, so keep them tight.
Order is always (south, west, north, east).
"""

AREAS: dict[str, tuple[float, float, float, float]] = {
    # United States
    "Austin, USA": (30.20, -97.80, 30.32, -97.68),
    "Denver, USA": (39.68, -105.02, 39.79, -104.90),
    "Miami, USA": (25.74, -80.24, 25.83, -80.16),
    "Seattle, USA": (47.58, -122.37, 47.67, -122.28),
    "Boston, USA": (42.33, -71.11, 42.39, -71.03),
    "Phoenix, USA": (33.42, -112.12, 33.52, -112.02),
    # United Kingdom
    "London, UK": (51.48, -0.16, 51.55, -0.06),
    "Manchester, UK": (53.45, -2.28, 53.51, -2.20),
    "Birmingham, UK": (52.45, -1.94, 52.51, -1.85),
    # Europe / EUR
    "Dublin, Ireland": (53.32, -6.31, 53.38, -6.22),
    "Amsterdam, Netherlands": (52.34, 4.85, 52.40, 4.94),
    "Berlin, Germany": (52.48, 13.35, 52.55, 13.45),
    "Munich, Germany": (48.11, 11.53, 48.16, 11.62),
    "Barcelona, Spain": (41.37, 2.14, 41.42, 2.21),
    # Other high-rate markets
    "Toronto, Canada": (43.63, -79.42, 43.70, -79.34),
    "Sydney, Australia": (-33.90, 151.17, -33.85, 151.24),
    # Local — available, not default
    "New Delhi, India": (28.55, 77.18, 28.65, 77.28),
}

DEFAULT_AREAS = [
    ("Austin, USA", AREAS["Austin, USA"]),
    ("London, UK", AREAS["London, UK"]),
    ("Dublin, Ireland", AREAS["Dublin, Ireland"]),
    ("Toronto, Canada", AREAS["Toronto, Canada"]),
]


def areas_for(names) -> list[tuple[str, tuple[float, float, float, float]]]:
    """Match on a city name prefix, so "Austin" finds "Austin, USA"."""
    if not names:
        return DEFAULT_AREAS
    wanted = [n.strip().lower() for n in names if n and n.strip()]
    if not wanted:
        return DEFAULT_AREAS
    return [
        (label, bbox)
        for label, bbox in AREAS.items()
        if any(label.lower().startswith(w) for w in wanted)
    ]
