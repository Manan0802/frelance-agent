from fastapi.testclient import TestClient
from backend.config import settings
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


def test_run_rejects_oversized_batch():
    create_all(engine)
    set_run_deps({"notify": lambda text: True})
    client = TestClient(app)
    r = client.post("/run", json={"targets": [{"name": f"B{i}"} for i in range(51)]})
    assert r.status_code == 400


def test_api_key_enforced_when_set(monkeypatch):
    create_all(engine)
    monkeypatch.setattr(settings, "api_key", "secret123")
    client = TestClient(app)
    # missing/wrong key -> 401
    assert client.post("/run", json={"targets": []}).status_code == 401
    # correct key -> allowed
    set_run_deps({"notify": lambda text: True})
    ok = client.post("/run", json={"targets": []}, headers={"X-API-Key": "secret123"})
    assert ok.status_code == 200

