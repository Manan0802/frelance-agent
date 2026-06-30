from fastapi.testclient import TestClient
from backend.database.connection import engine
from backend.database.models import create_all
from backend.main import app, set_run_deps


def test_run_and_approve():
    create_all(engine)
    set_run_deps(
        {
            "research": lambda t: {"research_summary": "x", "pain_points": "no site"},
            "match": lambda need, projects: projects[:1],
            "write": lambda t, r, p: {
                "draft_text": "Hi Acme",
                "personalization_score": 8.0,
                "portfolio_used": ["Site"],
            },
            "notify": lambda text: True,
        }
    )
    client = TestClient(app)
    r = client.post("/run", json={"targets": [{"name": "Acme", "address": "Delhi"}]})
    assert r.status_code == 200
    mid = r.json()["messages"][0]["id"]
    a = client.patch(f"/messages/{mid}/approve")
    assert a.status_code == 200
    assert a.json()["status"] == "approved"
