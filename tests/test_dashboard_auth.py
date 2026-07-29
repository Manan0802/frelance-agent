"""The dashboard is the whole pipeline in one page — business names, addresses,
email addresses and the drafts about to go to them. On localhost that's fine.
On a public URL it is a leak, so anything reachable from the internet has to be
behind a password.

The gate is off when no password is configured, so local work stays frictionless;
the deploy entrypoint refuses to boot without one, which is what stops a hosted
copy going out unprotected by accident.
"""

import base64

import pytest
from fastapi.testclient import TestClient

from backend.config import settings
from backend.database.connection import engine
from backend.database.models import create_all
from backend.main import app


def _auth(user: str, password: str) -> dict:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture
def guarded(monkeypatch):
    monkeypatch.setattr(settings, "dashboard_password", "s3cret")
    create_all(engine)
    return TestClient(app)


def test_no_password_configured_means_no_gate():
    """Local development is the common case and stays open."""
    create_all(engine)
    assert TestClient(app).get("/dashboard").status_code == 200


def test_a_configured_password_locks_the_dashboard(guarded):
    r = guarded.get("/dashboard")
    assert r.status_code == 401
    assert "basic" in r.headers.get("www-authenticate", "").lower()


def test_the_right_password_gets_in(guarded):
    assert guarded.get("/dashboard", headers=_auth("manan", "s3cret")).status_code == 200


def test_a_wrong_password_does_not(guarded):
    assert guarded.get("/dashboard", headers=_auth("manan", "guess")).status_code == 401


def test_the_approve_endpoints_are_guarded_too(guarded):
    """Approving is a state change. An open approve endpoint would let anyone
    who finds the URL mark drafts ready to send."""
    r = guarded.post("/dashboard/approve-all", json={"min_score": 7})
    assert r.status_code == 401


def test_deploying_without_a_password_is_refused():
    """The one mistake that would publish his pipeline — made impossible rather
    than documented."""
    from backend.api.dashboard import require_password_for_deploy

    with pytest.raises(RuntimeError, match="DASHBOARD_PASSWORD"):
        require_password_for_deploy("")

    require_password_for_deploy("set")  # does not raise
