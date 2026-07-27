from fastapi.testclient import TestClient
from backend.database.connection import engine
from backend.database.models import create_all
from backend.main import app, set_inbound_deps


def test_run_inbound():
    create_all(engine)
    set_inbound_deps(
        {
            "score": lambda job, pf: {"score": 90, "skill_matched": ["LangGraph"], "auto_rejected": False},
            "match": lambda need, projects: projects[:1],
            "write": lambda job, projects: {
                "draft_text": "Hi",
                "personalization_score": 8.0,
                "portfolio_used": [p.name for p in projects],
            },
            "notify": lambda text: True,
        }
    )
    client = TestClient(app)
    r = client.post("/run-inbound", json={"jobs": [{"source": "remoteok", "title": "LangGraph dev", "description": "RAG"}]})
    assert r.status_code == 200
    assert len(r.json()["proposals"]) == 1
    assert r.json()["proposals"][0]["score"] == 8.0


def test_run_inbound_fetches_sources_when_no_jobs_given(monkeypatch):
    """Without this, every fetcher is unreachable from the running app —
    jobs could only arrive by being hand-posted."""
    create_all(engine)
    import backend.api.routes as routes

    monkeypatch.setattr(
        routes, "collect_jobs",
        lambda: [{"source": "hn_freelance", "title": "Need an agent", "description": "LangGraph"}],
    )
    set_inbound_deps(
        {
            "score": lambda job, pf: {"score": 90, "skill_matched": [], "auto_rejected": False},
            "match": lambda need, projects: projects[:1],
            "write": lambda job, projects: {
                "draft_text": "Hi",
                "personalization_score": 8.0,
                "portfolio_used": [p.name for p in projects],
            },
            "notify": lambda text: True,
        }
    )
    client = TestClient(app)
    r = client.post("/run-inbound", json={})
    assert r.status_code == 200
    assert len(r.json()["proposals"]) == 1


def test_fetched_jobs_are_capped(monkeypatch):
    """A source returning hundreds of rows would otherwise fire an LLM scoring
    call per row on a single request."""
    create_all(engine)
    import backend.api.routes as routes

    monkeypatch.setattr(
        routes, "collect_jobs",
        lambda: [{"source": "s", "title": f"job{i}", "description": "d"} for i in range(500)],
    )
    seen = {"n": 0}

    def counting_score(job, pf):
        seen["n"] += 1
        return {"score": 10, "skill_matched": [], "auto_rejected": True}

    set_inbound_deps({"score": counting_score, "notify": lambda text: True})
    client = TestClient(app)
    r = client.post("/run-inbound", json={})
    assert r.status_code == 200
    assert seen["n"] <= routes.MAX_TARGETS
