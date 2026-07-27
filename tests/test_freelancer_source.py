"""Freelancer.com active-projects API.

The project's own research doc said this needed OAuth + application review. That
is true of the bidding/write API; the *read* endpoint answers with no
credentials at all (verified 200, live).

Two things make it the strongest source found: `budget.minimum/maximum` and
`currency.code` are structured, so "only USD/GBP/EUR work above $X" is an exact
filter rather than a regex guess. Unfiltered the feed is INR-heavy low-budget
work — precisely what Manan is trying to avoid — so the filters aren't optional.
"""

from backend.engine_a.freelancer import fetch_freelancer, HIGH_VALUE_CURRENCIES


def _project(**kw):
    base = {
        "id": 1,
        "title": "Build a website",
        "preview_description": "short",
        "description": "full description here",
        "seo_url": "web/Build-a-website",
        "currency": {"code": "USD"},
        "budget": {"minimum": 750.0, "maximum": 1500.0},
        "jobs": [{"name": "PHP"}, {"name": "WordPress"}],
        "location": {"country": {"name": None}},
    }
    base.update(kw)
    return base


def _http(projects):
    return lambda url: {"result": {"projects": projects}}


def test_keeps_high_currency_projects():
    rows = fetch_freelancer(http=_http([
        _project(id=1, currency={"code": "USD"}),
        _project(id=2, currency={"code": "EUR"}),
        _project(id=3, currency={"code": "GBP"}),
    ]))
    assert len(rows) == 3
    assert rows[0]["source"] == "freelancer"


def test_drops_low_currency_projects():
    """Manan's explicit priority: dollar/pound/euro work. INR listings are the
    low-rate flood this filter exists to keep out."""
    rows = fetch_freelancer(http=_http([
        _project(id=1, currency={"code": "INR"}),
        _project(id=2, currency={"code": "USD"}),
    ]))
    assert [r["title"] for r in rows] == ["Build a website"]
    assert len(rows) == 1


def test_budget_carries_currency_and_range():
    rows = fetch_freelancer(http=_http([_project(currency={"code": "EUR"},
                                                 budget={"minimum": 3000.0, "maximum": 5000.0})]))
    assert rows[0]["budget"] == "EUR 3000-5000"


def test_url_is_built_from_seo_url():
    rows = fetch_freelancer(http=_http([_project(seo_url="web/My-Project")]))
    assert rows[0]["url"] == "https://www.freelancer.com/projects/web/My-Project"


def test_description_prefers_full_over_preview():
    rows = fetch_freelancer(http=_http([_project(description="the full text",
                                                 preview_description="trunc")]))
    assert rows[0]["description"].startswith("the full text")


def test_skills_are_appended_so_matching_has_signal():
    rows = fetch_freelancer(http=_http([_project(jobs=[{"name": "Python"}, {"name": "LangChain"}])]))
    assert "Python" in rows[0]["description"] and "LangChain" in rows[0]["description"]


def test_client_country_used_as_location_when_present():
    rows = fetch_freelancer(http=_http([
        _project(location={"country": {"name": "United Kingdom"}}),
    ]))
    assert rows[0]["location"] == "United Kingdom"


def test_missing_country_leaves_location_empty_not_guessed():
    """Currency is not a country. Don't invent a location from it."""
    rows = fetch_freelancer(http=_http([_project(location={"country": {"name": None}})]))
    assert rows[0]["location"] == ""


def test_request_asks_the_api_to_filter_by_minimum_budget():
    """Filtering server-side keeps the INR/low-budget flood off the wire."""
    seen = {}

    def spy(url):
        seen["url"] = url
        return {"result": {"projects": []}}

    fetch_freelancer(http=spy, min_budget=500)
    assert "min_avg_price=500" in seen["url"]


def test_survives_a_malformed_project():
    rows = fetch_freelancer(http=_http([{"id": 1, "currency": {"code": "USD"}}]))
    assert rows[0]["title"] == ""
    assert rows[0]["budget"] is None


def test_high_value_currencies_cover_the_target_markets():
    assert {"USD", "GBP", "EUR"} <= HIGH_VALUE_CURRENCIES
    assert "INR" not in HIGH_VALUE_CURRENCIES


def test_hourly_and_fixed_budgets_are_judged_on_different_scales():
    """The API's min_avg_price applies to both alike, so a live pull returned
    "USD 2-8" and "USD 15-25" alongside "EUR 750-1500" — those small numbers
    are HOURLY RATES, not project budgets. Judged on one scale, either the junk
    gets through or real fixed-price work gets dropped."""
    rows = fetch_freelancer(
        http=_http([
            _project(id=1, type="hourly", budget={"minimum": 8.0, "maximum": 15.0}),
            _project(id=2, type="hourly", budget={"minimum": 60.0, "maximum": 90.0}),
            _project(id=3, type="fixed", budget={"minimum": 750.0, "maximum": 1500.0}),
            _project(id=4, type="fixed", budget={"minimum": 60.0, "maximum": 90.0}),
        ]),
        min_hourly=25,
        min_fixed=500,
    )
    kept = {r["budget"] for r in rows}
    assert kept == {"USD 60-90", "USD 750-1500"}, "cheap hourly and tiny fixed both dropped"


def test_hourly_rate_floor_defaults_below_his_target_band_but_above_junk():
    """His own pricing module puts him at $40-95/hr. The floor is a
    worth-an-LLM-call threshold, not his asking rate — set it too high and
    negotiable leads never get seen."""
    from backend.engine_a.freelancer import DEFAULT_MIN_HOURLY

    assert 15 < DEFAULT_MIN_HOURLY < 60


def test_projects_with_no_budget_are_kept_for_the_scorer_to_judge():
    rows = fetch_freelancer(http=_http([_project(budget={})]))
    assert len(rows) == 1 and rows[0]["budget"] is None
