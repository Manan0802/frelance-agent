"""Engine A had four fetchers (RemoteOK, WWR, JobSpy, HN) and nothing calling
them — jobs could only reach the pipeline by being hand-posted to /run-inbound,
so every fetcher was unreachable from the running app.

The aggregator fans them in. One source failing (network, API change, rate
limit) must not take the whole run down with it.
"""

from backend.engine_a.sources import collect_jobs, SOURCES


def test_collects_from_every_source():
    rows = collect_jobs(sources={
        "a": lambda: [{"source": "a", "title": "contract one"}],
        "b": lambda: [{"source": "b", "title": "freelance two"}],
    })
    assert {r["title"] for r in rows} == {"contract one", "freelance two"}


def test_one_failing_source_does_not_kill_the_run():
    def broken():
        raise RuntimeError("API changed")

    rows = collect_jobs(sources={
        "broken": broken,
        "ok": lambda: [{"source": "ok", "title": "contract survived"}],
    })
    assert [r["title"] for r in rows] == ["contract survived"]


def test_returns_empty_when_everything_fails():
    def broken():
        raise RuntimeError("down")

    assert collect_jobs(sources={"x": broken}) == []


def test_freelance_first_sources_are_registered_by_default():
    """Project scope is freelance/project work; HN's freelancer thread is the
    freelance-first source, the job boards are the deprioritised slice."""
    assert "hn_freelance" in SOURCES


def test_keeps_contract_and_freelance_listings_from_job_boards():
    from backend.engine_a.sources import is_freelance

    assert is_freelance({"title": "Contract React developer", "description": ""})
    assert is_freelance({"title": "Backend dev", "description": "6-month contract, project basis"})
    assert is_freelance({"title": "Freelance AI engineer", "description": ""})


def test_drops_full_time_employment_listings():
    """Employment is explicitly out of scope — Manan has a separate job agent."""
    from backend.engine_a.sources import is_freelance

    assert not is_freelance({"title": "Senior Engineer", "description": "Full-time role with benefits and equity"})
    assert not is_freelance({"title": "Junior Procurement Specialist", "description": "Manage vendor POs"})


def test_incidental_mentions_in_a_description_do_not_qualify():
    """Real WWR rows that slipped through a looser filter: long employment ads
    mention 'contract', 'consulting' or 'part-time' in passing (benefits
    boilerplate, team descriptions), which is not an engagement model."""
    from backend.engine_a.sources import is_freelance

    assert not is_freelance({
        "title": "Coinbase: Senior Sourcing Analyst",
        "description": "You will negotiate vendor contracts and manage consulting spend. Full-time.",
    })
    assert not is_freelance({
        "title": "Collibra: Director, Facility Security Officer",
        "description": "Oversee cleared personnel and contract compliance for federal programs.",
    })


def test_explicit_engagement_phrases_in_a_description_do_qualify():
    from backend.engine_a.sources import is_freelance

    assert is_freelance({"title": "Backend dev", "description": "This is a 6-month contract role, remote."})
    assert is_freelance({"title": "Web developer", "description": "Looking for a freelance developer for this project."})


def test_hn_freelance_posts_are_never_filtered_out():
    """That thread is freelance by definition; its posts rarely say the word."""
    from backend.engine_a.sources import is_freelance

    assert is_freelance({"source": "hn_freelance", "title": "SEEKING FREELANCER | Remote", "description": "Vue3 work"})


def test_collect_applies_the_freelance_filter():
    rows = collect_jobs(sources={
        "board": lambda: [
            {"source": "board", "title": "Contract Python dev", "description": ""},
            {"source": "board", "title": "Full-time Staff Engineer", "description": "permanent role"},
        ],
    })
    assert [r["title"] for r in rows] == ["Contract Python dev"]
