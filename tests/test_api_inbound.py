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
            "write": lambda job, projects: {"draft_text": "Hi", "personalization_score": 8.0},
            "notify": lambda text: True,
        }
    )
    client = TestClient(app)
    r = client.post("/run-inbound", json={"jobs": [{"source": "remoteok", "title": "LangGraph dev", "description": "RAG"}]})
    assert r.status_code == 200
    assert len(r.json()["proposals"]) == 1
    assert r.json()["proposals"][0]["score"] == 8.0
