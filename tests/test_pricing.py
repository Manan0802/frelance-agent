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
