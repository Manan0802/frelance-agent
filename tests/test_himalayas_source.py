"""Himalayas — free, no auth, ~96k jobs, and the same structured-field
advantage that made Remotive worthwhile: `employmentType`
(Full Time / Contractor / Part Time / Temporary), `locationRestrictions`,
and `minSalary`/`maxSalary`/`currency`/`salaryPeriod`.

The catch is density: only ~5-9% of listings are contract-shaped, and the API
caps at 20 per request regardless of the limit asked for. So it has to
paginate, and it has to page politely — this is a free service.
"""

from backend.engine_a.himalayas import fetch_himalayas, CONTRACT_TYPES


def _job(**kw):
    base = {
        "title": "Backend Engineer",
        "employmentType": "Contractor",
        "description": "build things",
        "applicationLink": "https://himalayas.app/x",
        "locationRestrictions": ["United States"],
        "minSalary": 90000,
        "maxSalary": 120000,
        "currency": "USD",
        "salaryPeriod": "annual",
        "companyName": "Acme",
    }
    base.update(kw)
    return base


def _pages(*pages):
    """Serve successive pages, then empty — the natural stop condition."""
    calls = {"n": 0}

    def http(url):
        i = calls["n"]
        calls["n"] += 1
        return {"jobs": list(pages[i]) if i < len(pages) else []}

    return http, calls


def test_keeps_only_contract_shaped_employment_types():
    http, _ = _pages([
        _job(title="a", employmentType="Contractor"),
        _job(title="b", employmentType="Full Time"),
        _job(title="c", employmentType="Part Time"),
        _job(title="d", employmentType="Temporary"),
    ])
    rows = fetch_himalayas(http=http, max_pages=1)
    assert {r["title"] for r in rows} == {"a", "c", "d"}


def test_paginates_until_a_page_comes_back_empty():
    http, calls = _pages([_job(title="p1")], [_job(title="p2")], [])
    rows = fetch_himalayas(http=http, max_pages=10)
    assert [r["title"] for r in rows] == ["p1", "p2"]
    assert calls["n"] == 3, "stops on the first empty page"


def test_respects_max_pages_so_a_free_api_is_not_hammered():
    http, calls = _pages(*[[_job(title=f"p{i}")] for i in range(20)])
    fetch_himalayas(http=http, max_pages=3)
    assert calls["n"] == 3


def test_offset_advances_between_pages():
    seen = []

    def http(url):
        seen.append(url)
        return {"jobs": [_job()] if len(seen) < 2 else []}

    fetch_himalayas(http=http, max_pages=5)
    assert "offset=0" in seen[0]
    assert "offset=20" in seen[1]


def test_location_restrictions_are_joined_into_a_location():
    http, _ = _pages([_job(locationRestrictions=["United States", "Canada"])])
    assert fetch_himalayas(http=http, max_pages=1)[0]["location"] == "United States, Canada"


def test_worldwide_when_no_restriction_given():
    """An unrestricted remote role is open to US/EU clients, so it should not
    read as 'unknown' — that would push it into the both-bands pricing path."""
    http, _ = _pages([_job(locationRestrictions=[])])
    assert fetch_himalayas(http=http, max_pages=1)[0]["location"] == "Worldwide"


def test_salary_is_formatted_with_currency_and_period():
    http, _ = _pages([_job(minSalary=90000, maxSalary=120000, currency="USD", salaryPeriod="annual")])
    assert fetch_himalayas(http=http, max_pages=1)[0]["budget"] == "USD 90000-120000 annual"


def test_missing_salary_is_none_not_a_broken_string():
    http, _ = _pages([_job(minSalary=None, maxSalary=None)])
    assert fetch_himalayas(http=http, max_pages=1)[0]["budget"] is None


def test_contract_types_exclude_full_time():
    assert "Full Time" not in CONTRACT_TYPES
    assert "Contractor" in CONTRACT_TYPES
