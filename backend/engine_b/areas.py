"""Prebuilt city bounding boxes for Overpass, so reaching volume doesn't mean
hand-writing coordinates.

Covers overseas and India both — Manan's scope is "overseas, India, sab jagah".
Defaults are USD/GBP/EUR markets because two dollar-paying clients are worth a
run of INR work, but Indian cities are one argument away (`areas_for(["India"])`).

Boxes are city-centre sized: Overpass times out on anything country-scale, and
it fails as a timeout rather than a clear error, so keep them tight.
Order is always (south, west, north, east).
"""

AREAS: dict[str, tuple[float, float, float, float]] = {
    # ---- United States (USD) ----
    "New York, USA": (40.70, -74.02, 40.78, -73.96),
    "San Francisco, USA": (37.76, -122.45, 37.81, -122.39),
    "Chicago, USA": (41.87, -87.65, 41.92, -87.61),
    "Austin, USA": (30.20, -97.80, 30.32, -97.68),
    "Denver, USA": (39.68, -105.02, 39.79, -104.90),
    "Miami, USA": (25.74, -80.24, 25.83, -80.16),
    "Seattle, USA": (47.58, -122.37, 47.67, -122.28),
    "Boston, USA": (42.33, -71.11, 42.39, -71.03),
    "Phoenix, USA": (33.42, -112.12, 33.52, -112.02),
    "Atlanta, USA": (33.74, -84.42, 33.80, -84.36),
    "Dallas, USA": (32.76, -96.83, 32.82, -96.76),
    # ---- United Kingdom (GBP) ----
    "London, UK": (51.48, -0.16, 51.55, -0.06),
    "Manchester, UK": (53.45, -2.28, 53.51, -2.20),
    "Birmingham, UK": (52.45, -1.94, 52.51, -1.85),
    "Leeds, UK": (53.77, -1.58, 53.82, -1.51),
    "Glasgow, UK": (55.84, -4.29, 55.89, -4.22),
    # ---- Europe (EUR) ----
    "Dublin, Ireland": (53.32, -6.31, 53.38, -6.22),
    "Amsterdam, Netherlands": (52.34, 4.85, 52.40, 4.94),
    "Berlin, Germany": (52.48, 13.35, 52.55, 13.45),
    "Munich, Germany": (48.11, 11.53, 48.16, 11.62),
    "Hamburg, Germany": (53.53, 9.96, 53.58, 10.04),
    "Paris, France": (48.84, 2.31, 48.89, 2.39),
    "Barcelona, Spain": (41.37, 2.14, 41.42, 2.21),
    "Madrid, Spain": (40.40, -3.72, 40.45, -3.66),
    "Milan, Italy": (45.45, 9.16, 45.50, 9.23),
    "Lisbon, Portugal": (38.71, -9.16, 38.75, -9.12),
    "Stockholm, Sweden": (59.31, 18.02, 59.36, 18.10),
    "Zurich, Switzerland": (47.36, 8.51, 47.40, 8.56),
    # ---- Other high-rate markets ----
    "Toronto, Canada": (43.63, -79.42, 43.70, -79.34),
    "Vancouver, Canada": (49.26, -123.14, 49.30, -123.09),
    "Sydney, Australia": (-33.90, 151.17, -33.85, 151.24),
    "Melbourne, Australia": (-37.83, 144.94, -37.79, 145.00),
    "Auckland, New Zealand": (-36.87, 174.74, -36.83, 174.80),
    "Singapore, Singapore": (1.27, 103.83, 1.32, 103.88),
    "Dubai, UAE": (25.18, 55.25, 25.24, 55.32),
    # ---- India (INR) — available, not default ----
    "Mumbai, India": (18.92, 72.81, 19.00, 72.88),
    "New Delhi, India": (28.55, 77.18, 28.65, 77.28),
    "Gurugram, India": (28.44, 77.03, 28.50, 77.10),
    "Noida, India": (28.55, 77.32, 28.62, 77.40),
    "Bengaluru, India": (12.94, 77.58, 13.00, 77.65),
    "Hyderabad, India": (17.40, 78.44, 17.46, 78.50),
    "Pune, India": (18.50, 73.82, 18.56, 73.89),
    "Chennai, India": (13.03, 80.23, 13.09, 80.28),
    "Ahmedabad, India": (23.01, 72.55, 23.07, 72.61),
    "Kolkata, India": (22.53, 88.33, 22.59, 88.39),
}

DEFAULT_AREAS = [
    ("Austin, USA", AREAS["Austin, USA"]),
    ("London, UK", AREAS["London, UK"]),
    ("Dublin, Ireland", AREAS["Dublin, Ireland"]),
    ("Toronto, Canada", AREAS["Toronto, Canada"]),
]


def areas_for(names) -> list[tuple[str, tuple[float, float, float, float]]]:
    """Match a city name prefix ("Austin") or a country suffix ("India"), so
    whole markets can be selected as easily as single cities."""
    if not names:
        return DEFAULT_AREAS
    wanted = [n.strip().lower() for n in names if n and n.strip()]
    if not wanted:
        return DEFAULT_AREAS
    return [
        (label, bbox)
        for label, bbox in AREAS.items()
        if any(label.lower().startswith(w) or label.lower().endswith(w) for w in wanted)
    ]
