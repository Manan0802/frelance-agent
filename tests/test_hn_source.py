"""HN "Ask HN: Freelancer? Seeking freelancer?" monthly thread.

Measured reality (4 threads, Apr-Jul 2026, ~87 top-level comments): only ONE
was "SEEKING FREELANCER" (a client hiring). Everything else is "SEEKING WORK" —
other freelancers advertising themselves, i.e. competitors, not leads.

So the filter is the whole feature. Ingesting the thread naively would feed
~85 competitor ads into Engine A as jobs, burning an LLM scoring call on each.
"""

from backend.engine_a.hn_source import fetch_hn_freelance, _is_seeking_freelancer


def test_keeps_only_clients_who_are_hiring():
    assert _is_seeking_freelancer("SEEKING FREELANCER | Remote | Need a React dev")
    assert _is_seeking_freelancer("seeking freelancer - backend work")


def test_rejects_freelancers_advertising_themselves():
    assert not _is_seeking_freelancer("SEEKING WORK | Remote | I am a full-stack dev")
    assert not _is_seeking_freelancer("SEEKING WORK, Canada, remote if possible")


def test_only_matches_the_marker_near_the_start():
    """A SEEKING WORK ad that merely mentions the phrase later must not slip in."""
    text = "SEEKING WORK | Remote. " + "x" * 300 + " seeking freelancer"
    assert not _is_seeking_freelancer(text)


def test_fetch_maps_hiring_comments_to_the_common_job_shape():
    def fake_search(url):
        return {"hits": [{"objectID": "111", "title": "Ask HN: Freelancer? Seeking freelancer? (July 2026)"}]}

    def fake_item(url):
        assert "111" in url
        return {
            "children": [
                {"id": 1, "author": "client1", "text": "SEEKING FREELANCER | Remote | Need a <b>LangGraph</b> agent built. Budget $5k."},
                {"id": 2, "author": "dev1", "text": "SEEKING WORK | I am a React developer with 10 years."},
                {"id": 3, "author": None, "text": None},
            ]
        }

    rows = fetch_hn_freelance(search=fake_search, item=fake_item)

    assert len(rows) == 1, "only the hiring post is a lead"
    r = rows[0]
    assert r["source"] == "hn_freelance"
    assert "LangGraph" in r["description"]
    assert "<b>" not in r["description"], "HTML must be stripped"
    assert r["url"] == "https://news.ycombinator.com/item?id=1"


def test_decodes_html_entities():
    def fake_search(url):
        return {"hits": [{"objectID": "1", "title": "Ask HN: Freelancer? Seeking freelancer? (July 2026)"}]}

    def fake_item(url):
        return {"children": [{"id": 9, "author": "c", "text": "SEEKING FREELANCER | Need Python&#x2F;React work &amp; testing"}]}

    rows = fetch_hn_freelance(search=fake_search, item=fake_item)
    assert "Python/React" in rows[0]["description"]
    assert "&" in rows[0]["description"] and "&amp;" not in rows[0]["description"]


def test_ignores_threads_that_are_not_the_freelancer_thread():
    def fake_search(url):
        return {"hits": [
            {"objectID": "1", "title": "Show HN: Mnml.page - one-page websites for freelancers"},
            {"objectID": "2", "title": "Ask HN: Who is hiring? (July 2026)"},
        ]}

    def fake_item(url):
        raise AssertionError("must not fetch unrelated threads")

    assert fetch_hn_freelance(search=fake_search, item=fake_item) == []
