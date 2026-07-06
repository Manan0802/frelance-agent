from fastapi.testclient import TestClient

from backend.database.connection import engine
from backend.database.models import create_all
from backend.main import app, set_run_deps, set_inbound_deps


def _seed_message(client):
    set_run_deps(
        {
            "research": lambda t: {"research_summary": "x", "pain_points": "no site"},
            "match": lambda need, projects: projects[:1],
            "write": lambda t, r, p: {
                "draft_text": "Hi Acme, noticed your site is down.",
                "personalization_score": 8.0,
                "portfolio_used": ["Site"],
            },
            "notify": lambda text: True,
        }
    )
    r = client.post("/run", json={"targets": [{"name": "Acme Bakery", "address": "Delhi"}]})
    return r.json()["messages"][0]["id"]


def _seed_proposal(client):
    set_inbound_deps(
        {
            "score": lambda job, pf: {"score": 90, "skill_matched": ["LangGraph"], "auto_rejected": False},
            "match": lambda need, projects: projects[:1],
            "write": lambda job, projects: {"draft_text": "Hi, I can build this RAG pipeline.", "personalization_score": 9.0},
            "notify": lambda text: True,
        }
    )
    r = client.post("/run-inbound", json={"jobs": [{"source": "remoteok", "title": "LangGraph dev", "description": "RAG"}]})
    return r.json()["proposals"][0]["id"]


def test_dashboard_empty_state():
    create_all(engine)
    client = TestClient(app)
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "no outbound messages yet" in r.text.lower()
    assert "no inbound proposals yet" in r.text.lower()


def test_dashboard_lists_messages_and_proposals():
    create_all(engine)
    client = TestClient(app)
    _seed_message(client)
    _seed_proposal(client)

    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "Acme Bakery" in r.text
    assert "LangGraph dev" in r.text
    assert "Hi Acme, noticed your site is down." in r.text


def test_dashboard_approve_message_updates_in_place():
    create_all(engine)
    client = TestClient(app)
    mid = _seed_message(client)

    r = client.patch(f"/dashboard/messages/{mid}/approve")
    assert r.status_code == 200
    assert "approved" in r.text.lower()

    # status is reflected on a full page load too
    page = client.get("/dashboard")
    assert "approved" in page.text.lower()


def test_dashboard_approve_proposal_updates_in_place():
    create_all(engine)
    client = TestClient(app)
    pid = _seed_proposal(client)

    r = client.patch(f"/dashboard/proposals/{pid}/approve")
    assert r.status_code == 200
    assert "approved" in r.text.lower()
