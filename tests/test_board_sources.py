"""Remotive + Working Nomads: free, no-auth boards whose listings skew US/EU.

Manan's targeting priority is USD/GBP/EUR clients — two of those are worth more
than a run of INR work — so these sources must carry location through, not just
title and description.

Remotive is the better of the two: it exposes a structured `job_type`
(full_time / contract / freelance / part_time), so its freelance filter is
exact rather than the regex guess the other boards need.
"""

from backend.engine_a.remotive import fetch_remotive
from backend.engine_a.workingnomads import fetch_working_nomads


def test_remotive_keeps_only_contract_and_freelance():
    def fake_http(url):
        return {"jobs": [
            {"id": 1, "title": "Senior Independent AI Engineer", "job_type": "contract",
             "description": "<p>Build agents</p>", "url": "u1",
             "candidate_required_location": "Americas, Europe", "salary": "$120 - $170 /hour"},
            {"id": 2, "title": "Freelance Writer", "job_type": "freelance",
             "description": "d", "url": "u2", "candidate_required_location": "Worldwide", "salary": ""},
            {"id": 3, "title": "Staff Engineer", "job_type": "full_time",
             "description": "d", "url": "u3", "candidate_required_location": "USA", "salary": "$200k"},
        ]}

    rows = fetch_remotive(http=fake_http)

    assert [r["title"] for r in rows] == ["Senior Independent AI Engineer", "Freelance Writer"]
    assert rows[0]["source"] == "remotive"
    assert rows[0]["location"] == "Americas, Europe"
    assert rows[0]["budget"] == "$120 - $170 /hour"
    assert "<p>" not in rows[0]["description"], "HTML must be stripped"


def test_remotive_carries_no_budget_as_none_not_empty_string():
    def fake_http(url):
        return {"jobs": [{"id": 1, "title": "t", "job_type": "contract", "description": "d",
                          "url": "u", "candidate_required_location": "USA", "salary": ""}]}

    assert fetch_remotive(http=fake_http)[0]["budget"] is None


def test_working_nomads_maps_to_the_common_shape():
    def fake_http(url):
        return [{"title": "Senior UI Designer", "description": "<b>design</b> work",
                 "url": "https://x", "location": "Europe, North America", "company_name": "Acme"}]

    rows = fetch_working_nomads(http=fake_http)

    assert rows[0]["source"] == "workingnomads"
    assert rows[0]["location"] == "Europe, North America"
    assert "<b>" not in rows[0]["description"]
    assert rows[0]["budget"] is None


def test_both_sources_survive_missing_fields():
    assert fetch_remotive(http=lambda u: {"jobs": [{"job_type": "contract"}]})[0]["title"] == ""
    assert fetch_working_nomads(http=lambda u: [{}])[0]["location"] == ""
