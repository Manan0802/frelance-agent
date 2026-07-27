from backend.pricing.suggest import suggest_rate


def test_suggest_rate_agentic_high_geography():
    r = suggest_rate(is_agentic=True, client_geography="US")
    assert r["suggested_rate_usd_per_hr"] == (60, 95)
    assert r["tier"] == "high"


def test_suggest_rate_agentic_other_geography_is_lower():
    r = suggest_rate(is_agentic=True, client_geography="India")
    low, high = r["suggested_rate_usd_per_hr"]
    assert low < 60
    assert high < 95
    assert r["tier"] == "other"


def test_suggest_rate_full_stack_lower_than_agentic():
    agentic = suggest_rate(is_agentic=True, client_geography="UK")
    full_stack = suggest_rate(is_agentic=False, client_geography="UK")
    assert full_stack["suggested_rate_usd_per_hr"][1] < agentic["suggested_rate_usd_per_hr"][1]


def test_suggest_rate_unknown_geography_defaults_to_other_tier():
    r = suggest_rate(is_agentic=True, client_geography="")
    assert r["tier"] == "other"


def test_suggest_rate_is_case_insensitive_on_geography():
    r = suggest_rate(is_agentic=True, client_geography="united States")
    assert r["tier"] == "high"


def test_tiering_is_an_exception_list_not_a_rich_country_whitelist():
    """Manan's framing: ~120-130 currencies are stronger than the rupee, so
    almost everywhere pays better than local work. A whitelist of ~30 Western
    countries silently discounted the rest of the world.

    (One nuance the whitelist also got wrong: per-unit currency strength is the
    wrong test. The yen is "weaker" than the rupee per unit, yet Japanese rates
    are far higher. The tier tracks prevailing dev rates, not exchange rates.)"""
    from backend.pricing.suggest import high_tier_geography

    for market in ("Japan", "South Korea", "Israel", "Hong Kong", "Taiwan",
                   "Norway", "Sweden", "Denmark", "Finland", "Austria",
                   "Belgium", "Italy", "Spain", "Portugal", "Qatar",
                   "Saudi Arabia", "Kuwait", "Czechia", "Poland", "Croatia",
                   "Estonia", "Chile", "Uruguay", "Panama", "Costa Rica",
                   "Malaysia", "Thailand", "Mexico", "Brazil", "South Africa"):
        assert high_tier_geography(market), f"{market} should be high tier"


def test_markets_at_or_below_indian_rates_stay_on_the_other_tier():
    from backend.pricing.suggest import high_tier_geography

    for market in ("India", "Pakistan", "Bangladesh", "Nepal", "Sri Lanka",
                   "Nigeria", "Kenya", "Ghana", "Uganda", "Ethiopia"):
        assert not high_tier_geography(market), f"{market} should not be high tier"


def test_lower_rate_cities_are_recognised_without_the_country_name():
    """Engine B targets carry whatever the source gave — often a bare city or
    street address, not "City, Country". A country-only exception list quoted a
    Delhi client the premium band."""
    from backend.pricing.suggest import high_tier_geography

    for city in ("Delhi", "Mumbai", "Bengaluru", "Gurugram", "Noida", "Pune",
                 "Hyderabad", "Chennai", "Kolkata", "Karachi", "Lahore",
                 "Dhaka", "Lagos", "Nairobi"):
        assert not high_tier_geography(city), f"{city} should not be high tier"


def test_a_lower_rate_city_is_caught_inside_a_full_address():
    from backend.pricing.suggest import high_tier_geography

    assert not high_tier_geography("12 Hauz Khas, New Delhi, 110016")


def test_a_named_place_not_on_the_exception_list_is_high_tier():
    """That's the whole point of the exception model — most of the world pays
    above Indian rates, so an unrecognised city is high tier by default."""
    from backend.pricing.suggest import high_tier_geography

    assert high_tier_geography("Springfield")
    assert high_tier_geography("Ljubljana, Slovenia")


def test_no_stated_geography_stays_on_the_conservative_band():
    """With no place named at all there's nothing to reason from, and quoting
    the premium band would be a guess."""
    from backend.pricing.suggest import high_tier_geography

    assert not high_tier_geography("")
    assert not high_tier_geography("   ")


def test_two_letter_country_codes_are_understood():
    """Boards write "US", "UK", "UAE" — a 3-letters-minimum rule silently
    dropped all of them onto the discounted band."""
    from backend.pricing.suggest import high_tier_geography

    for code in ("US", "UK", "UAE", "NZ", "SG"):
        assert high_tier_geography(code), f"{code} should be high tier"
