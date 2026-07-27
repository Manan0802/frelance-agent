"""Global target cities for Engine B.

Every continent — Manan's scope is "North America, Europe, Australia, Asia,
South America, Africa". Cities are stored as a **centre point** and the bounding
box is derived, rather than four hand-written numbers each: hundreds of entries
stay reviewable, and one mistyped coordinate can't silently produce an inverted
or planet-sized box.

Defaults are USD/GBP/EUR markets, since two dollar-paying clients are worth a
run of INR work — but any city or whole country is one argument away:
`areas_for(["India"])`, `areas_for(["Berlin", "Brazil"])`.

Boxes are deliberately city-centre sized. Overpass times out on anything
country-scale, and it fails as a timeout rather than a clear error.
"""

import math

# Half-height of a city box, in degrees of latitude (~5.5 km each way).
BOX_RADIUS_DEG = 0.05

CITIES: dict[str, tuple[float, float]] = {
    # ---------- North America ----------
    "New York, USA": (40.7128, -74.0060),
    "Los Angeles, USA": (34.0522, -118.2437),
    "Chicago, USA": (41.8781, -87.6298),
    "Houston, USA": (29.7604, -95.3698),
    "Phoenix, USA": (33.4484, -112.0740),
    "Philadelphia, USA": (39.9526, -75.1652),
    "San Antonio, USA": (29.4241, -98.4936),
    "San Diego, USA": (32.7157, -117.1611),
    "Dallas, USA": (32.7767, -96.7970),
    "Austin, USA": (30.2672, -97.7431),
    "San Jose, USA": (37.3382, -121.8863),
    "San Francisco, USA": (37.7749, -122.4194),
    "Seattle, USA": (47.6062, -122.3321),
    "Denver, USA": (39.7392, -104.9903),
    "Boston, USA": (42.3601, -71.0589),
    "Atlanta, USA": (33.7490, -84.3880),
    "Miami, USA": (25.7617, -80.1918),
    "Tampa, USA": (27.9506, -82.4572),
    "Orlando, USA": (28.5383, -81.3792),
    "Charlotte, USA": (35.2271, -80.8431),
    "Nashville, USA": (36.1627, -86.7816),
    "Portland, USA": (45.5152, -122.6784),
    "Las Vegas, USA": (36.1699, -115.1398),
    "Minneapolis, USA": (44.9778, -93.2650),
    "Detroit, USA": (42.3314, -83.0458),
    "Columbus, USA": (39.9612, -82.9988),
    "Pittsburgh, USA": (40.4406, -79.9959),
    "Salt Lake City, USA": (40.7608, -111.8910),
    "Kansas City, USA": (39.0997, -94.5786),
    "Raleigh, USA": (35.7796, -78.6382),
    "Toronto, Canada": (43.6532, -79.3832),
    "Vancouver, Canada": (49.2827, -123.1207),
    "Montreal, Canada": (45.5017, -73.5673),
    "Calgary, Canada": (51.0447, -114.0719),
    "Ottawa, Canada": (45.4215, -75.6972),
    "Edmonton, Canada": (53.5461, -113.4938),
    "Mexico City, Mexico": (19.4326, -99.1332),
    "Guadalajara, Mexico": (20.6597, -103.3496),
    "Monterrey, Mexico": (25.6866, -100.3161),
    # ---------- United Kingdom & Ireland ----------
    "London, UK": (51.5074, -0.1278),
    "Manchester, UK": (53.4808, -2.2426),
    "Birmingham, UK": (52.4862, -1.8904),
    "Leeds, UK": (53.8008, -1.5491),
    "Glasgow, UK": (55.8642, -4.2518),
    "Edinburgh, UK": (55.9533, -3.1883),
    "Bristol, UK": (51.4545, -2.5879),
    "Liverpool, UK": (53.4084, -2.9916),
    "Cardiff, UK": (51.4816, -3.1791),
    "Belfast, UK": (54.5973, -5.9301),
    "Dublin, Ireland": (53.3498, -6.2603),
    "Cork, Ireland": (51.8985, -8.4756),
    # ---------- Europe ----------
    "Berlin, Germany": (52.5200, 13.4050),
    "Munich, Germany": (48.1351, 11.5820),
    "Hamburg, Germany": (53.5511, 9.9937),
    "Frankfurt, Germany": (50.1109, 8.6821),
    "Cologne, Germany": (50.9375, 6.9603),
    "Stuttgart, Germany": (48.7758, 9.1829),
    "Dusseldorf, Germany": (51.2277, 6.7735),
    "Paris, France": (48.8566, 2.3522),
    "Lyon, France": (45.7640, 4.8357),
    "Marseille, France": (43.2965, 5.3698),
    "Toulouse, France": (43.6047, 1.4442),
    "Amsterdam, Netherlands": (52.3676, 4.9041),
    "Rotterdam, Netherlands": (51.9244, 4.4777),
    "Eindhoven, Netherlands": (51.4416, 5.4697),
    "Brussels, Belgium": (50.8503, 4.3517),
    "Antwerp, Belgium": (51.2194, 4.4025),
    "Madrid, Spain": (40.4168, -3.7038),
    "Barcelona, Spain": (41.3851, 2.1734),
    "Valencia, Spain": (39.4699, -0.3763),
    "Seville, Spain": (37.3891, -5.9845),
    "Milan, Italy": (45.4642, 9.1900),
    "Rome, Italy": (41.9028, 12.4964),
    "Turin, Italy": (45.0703, 7.6869),
    "Bologna, Italy": (44.4949, 11.3426),
    "Lisbon, Portugal": (38.7223, -9.1393),
    "Porto, Portugal": (41.1579, -8.6291),
    "Zurich, Switzerland": (47.3769, 8.5417),
    "Geneva, Switzerland": (46.2044, 6.1432),
    "Vienna, Austria": (48.2082, 16.3738),
    "Stockholm, Sweden": (59.3293, 18.0686),
    "Gothenburg, Sweden": (57.7089, 11.9746),
    "Copenhagen, Denmark": (55.6761, 12.5683),
    "Oslo, Norway": (59.9139, 10.7522),
    "Helsinki, Finland": (60.1699, 24.9384),
    "Warsaw, Poland": (52.2297, 21.0122),
    "Krakow, Poland": (50.0647, 19.9450),
    "Prague, Czechia": (50.0755, 14.4378),
    "Budapest, Hungary": (47.4979, 19.0402),
    "Bucharest, Romania": (44.4268, 26.1025),
    "Athens, Greece": (37.9838, 23.7275),
    "Sofia, Bulgaria": (42.6977, 23.3219),
    "Zagreb, Croatia": (45.8150, 15.9819),
    "Tallinn, Estonia": (59.4370, 24.7536),
    "Vilnius, Lithuania": (54.6872, 25.2797),
    "Riga, Latvia": (56.9496, 24.1052),
    # ---------- Middle East ----------
    "Dubai, UAE": (25.2048, 55.2708),
    "Abu Dhabi, UAE": (24.4539, 54.3773),
    "Doha, Qatar": (25.2854, 51.5310),
    "Riyadh, Saudi Arabia": (24.7136, 46.6753),
    "Jeddah, Saudi Arabia": (21.4858, 39.1925),
    "Tel Aviv, Israel": (32.0853, 34.7818),
    "Amman, Jordan": (31.9454, 35.9284),
    "Kuwait City, Kuwait": (29.3759, 47.9774),
    "Manama, Bahrain": (26.2285, 50.5860),
    "Muscat, Oman": (23.5880, 58.3829),
    # ---------- India ----------
    "Mumbai, India": (19.0760, 72.8777),
    "New Delhi, India": (28.6139, 77.2090),
    "Gurugram, India": (28.4595, 77.0266),
    "Noida, India": (28.5355, 77.3910),
    "Bengaluru, India": (12.9716, 77.5946),
    "Hyderabad, India": (17.3850, 78.4867),
    "Pune, India": (18.5204, 73.8567),
    "Chennai, India": (13.0827, 80.2707),
    "Kolkata, India": (22.5726, 88.3639),
    "Ahmedabad, India": (23.0225, 72.5714),
    "Jaipur, India": (26.9124, 75.7873),
    "Surat, India": (21.1702, 72.8311),
    "Lucknow, India": (26.8467, 80.9462),
    "Indore, India": (22.7196, 75.8577),
    "Chandigarh, India": (30.7333, 76.7794),
    "Kochi, India": (9.9312, 76.2673),
    "Coimbatore, India": (11.0168, 76.9558),
    "Nagpur, India": (21.1458, 79.0882),
    "Bhopal, India": (23.2599, 77.4126),
    "Visakhapatnam, India": (17.6868, 83.2185),
    "Thane, India": (19.2183, 72.9781),
    "Vadodara, India": (22.3072, 73.1812),
    "Nashik, India": (19.9975, 73.7898),
    "Ludhiana, India": (30.9010, 75.8573),
    "Agra, India": (27.1767, 78.0081),
    "Varanasi, India": (25.3176, 82.9739),
    "Patna, India": (25.5941, 85.1376),
    "Bhubaneswar, India": (20.2961, 85.8245),
    "Guwahati, India": (26.1445, 91.7362),
    "Mysuru, India": (12.2958, 76.6394),
    "Madurai, India": (9.9252, 78.1198),
    "Rajkot, India": (22.3039, 70.8022),
    "Dehradun, India": (30.3165, 78.0322),
    "Raipur, India": (21.2514, 81.6296),
    "Ranchi, India": (23.3441, 85.3096),
    "Amritsar, India": (31.6340, 74.8723),
    "Jodhpur, India": (26.2389, 73.0243),
    "Trivandrum, India": (8.5241, 76.9366),
    "Vijayawada, India": (16.5062, 80.6480),
    # ---------- Asia-Pacific ----------
    "Singapore, Singapore": (1.3521, 103.8198),
    "Kuala Lumpur, Malaysia": (3.1390, 101.6869),
    "Bangkok, Thailand": (13.7563, 100.5018),
    "Jakarta, Indonesia": (-6.2088, 106.8456),
    "Manila, Philippines": (14.5995, 120.9842),
    "Ho Chi Minh City, Vietnam": (10.8231, 106.6297),
    "Hanoi, Vietnam": (21.0278, 105.8342),
    "Tokyo, Japan": (35.6762, 139.6503),
    "Osaka, Japan": (34.6937, 135.5023),
    "Yokohama, Japan": (35.4437, 139.6380),
    "Fukuoka, Japan": (33.5904, 130.4017),
    "Seoul, South Korea": (37.5665, 126.9780),
    "Busan, South Korea": (35.1796, 129.0756),
    "Hong Kong, Hong Kong": (22.3193, 114.1694),
    "Taipei, Taiwan": (25.0330, 121.5654),
    "Colombo, Sri Lanka": (6.9271, 79.8612),
    "Dhaka, Bangladesh": (23.8103, 90.4125),
    "Karachi, Pakistan": (24.8607, 67.0011),
    "Lahore, Pakistan": (31.5204, 74.3587),
    "Kathmandu, Nepal": (27.7172, 85.3240),
    # ---------- Oceania ----------
    "Sydney, Australia": (-33.8688, 151.2093),
    "Melbourne, Australia": (-37.8136, 144.9631),
    "Brisbane, Australia": (-27.4698, 153.0251),
    "Perth, Australia": (-31.9505, 115.8605),
    "Adelaide, Australia": (-34.9285, 138.6007),
    "Canberra, Australia": (-35.2809, 149.1300),
    "Gold Coast, Australia": (-28.0167, 153.4000),
    "Auckland, New Zealand": (-36.8485, 174.7633),
    "Wellington, New Zealand": (-41.2865, 174.7762),
    "Christchurch, New Zealand": (-43.5321, 172.6362),
    # ---------- South America ----------
    "Sao Paulo, Brazil": (-23.5505, -46.6333),
    "Rio de Janeiro, Brazil": (-22.9068, -43.1729),
    "Belo Horizonte, Brazil": (-19.9167, -43.9345),
    "Porto Alegre, Brazil": (-30.0346, -51.2177),
    "Curitiba, Brazil": (-25.4284, -49.2733),
    "Buenos Aires, Argentina": (-34.6037, -58.3816),
    "Cordoba, Argentina": (-31.4201, -64.1888),
    "Santiago, Chile": (-33.4489, -70.6693),
    "Bogota, Colombia": (4.7110, -74.0721),
    "Medellin, Colombia": (6.2442, -75.5812),
    "Lima, Peru": (-12.0464, -77.0428),
    "Montevideo, Uruguay": (-34.9011, -56.1645),
    "Quito, Ecuador": (-0.1807, -78.4678),
    "San Jose, Costa Rica": (9.9281, -84.0907),
    "Panama City, Panama": (8.9824, -79.5199),
    # ---------- Africa ----------
    "Johannesburg, South Africa": (-26.2041, 28.0473),
    "Cape Town, South Africa": (-33.9249, 18.4241),
    "Durban, South Africa": (-29.8587, 31.0218),
    "Pretoria, South Africa": (-25.7479, 28.2293),
    "Lagos, Nigeria": (6.5244, 3.3792),
    "Abuja, Nigeria": (9.0765, 7.3986),
    "Nairobi, Kenya": (-1.2921, 36.8219),
    "Mombasa, Kenya": (-4.0435, 39.6682),
    "Accra, Ghana": (5.6037, -0.1870),
    "Cairo, Egypt": (30.0444, 31.2357),
    "Casablanca, Morocco": (33.5731, -7.5898),
    "Tunis, Tunisia": (36.8065, 10.1815),
    "Kigali, Rwanda": (-1.9441, 30.0619),
    "Dar es Salaam, Tanzania": (-6.7924, 39.2083),
    "Kampala, Uganda": (0.3476, 32.5825),
    "Addis Ababa, Ethiopia": (9.0320, 38.7469),
    # ---------- Further high-rate markets ----------
    "Luxembourg, Luxembourg": (49.6116, 6.1319),
    "Bratislava, Slovakia": (48.1486, 17.1077),
    "Ljubljana, Slovenia": (46.0569, 14.5058),
    "Belgrade, Serbia": (44.7866, 20.4489),
    "Reykjavik, Iceland": (64.1466, -21.9426),
    "Valletta, Malta": (35.8989, 14.5146),
    "Nicosia, Cyprus": (35.1856, 33.3823),
    "Istanbul, Turkey": (41.0082, 28.9784),
}


def bbox_for(lat: float, lon: float, radius_deg: float = BOX_RADIUS_DEG):
    """A degree of longitude shrinks towards the poles, so widen it by
    1/cos(latitude) — otherwise a fixed-degree box covers far less ground in
    Stockholm than in Singapore."""
    lon_radius = radius_deg / max(math.cos(math.radians(lat)), 0.2)
    return (
        round(lat - radius_deg, 4),
        round(lon - lon_radius, 4),
        round(lat + radius_deg, 4),
        round(lon + lon_radius, 4),
    )


AREAS: dict[str, tuple[float, float, float, float]] = {
    label: bbox_for(lat, lon) for label, (lat, lon) in CITIES.items()
}

COUNTRIES = sorted({label.split(", ", 1)[1] for label in CITIES})

DEFAULT_AREAS = [
    (label, AREAS[label])
    for label in ("Austin, USA", "London, UK", "Dublin, Ireland", "Toronto, Canada")
]


def areas_for(names) -> list[tuple[str, tuple[float, float, float, float]]]:
    """Match a city prefix ("Austin") or a country suffix ("India"), so whole
    markets are as easy to select as single cities."""
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
