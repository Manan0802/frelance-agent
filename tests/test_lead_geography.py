"""Geography has to survive the whole pipeline.

Manan's targeting priority is USD/GBP/EUR clients. Until now JobLead had no
location column, so inbound proposals showed both pricing bands with
"geography unknown" — even when the source (Remotive, Working Nomads) told us
exactly where the client is. Carrying it means the rate shown is the real one,
and high-currency leads are visible at a glance.
"""

from fastapi.testclient import TestClient

from backend.database.connection import engine, SessionLocal
from backend.database.models import create_all, JobLead
from backend.portfolio.context import PortfolioContext, PortfolioProject
from backend.engine_a.graph import run_engine_a
from backend.main import app, set_inbound_deps
from backend.pricing.suggest import high_tier_geography


PF = PortfolioContext(
    personal={"name": "Manan"},
    projects=[PortfolioProject(name="SARA", type="ai_ml", description="agents", pitch_for=["AI agent"])],
)

DEPS = {
    "score": lambda job, pf: {"score": 90, "skill_matched": [], "auto_rejected": False},
    "match": lambda need, projects: projects[:1],
    "write": lambda job, projects: {"draft_text": "Hi", "personalization_score": 8.0,
                                    "portfolio_used": [p.name for p in projects]},
    "notify": lambda text: True,
}


def test_location_is_persisted_on_the_lead():
    create_all(engine)
    db = SessionLocal()
    run_engine_a(
        [{"source": "remotive", "title": "AI Engineer", "description": "agents",
          "location": "Americas, Europe"}],
        db, PF, deps=DEPS,
    )
    assert db.query(JobLead).first().location == "Americas, Europe"
    db.close()


def test_missing_location_is_not_fatal():
    create_all(engine)
    db = SessionLocal()
    run_engine_a([{"source": "hn_freelance", "title": "t", "description": "d"}], db, PF, deps=DEPS)
    assert db.query(JobLead).first().location == ""
    db.close()


def test_high_tier_detected_from_multi_region_strings():
    """Boards give regions, not countries: 'Americas, Europe', 'USA', 'Worldwide'."""
    assert high_tier_geography("Americas, Europe, Israel")
    assert high_tier_geography("USA")
    assert high_tier_geography("Northern America, Europe, UK")
    assert not high_tier_geography("India")
    assert not high_tier_geography("")


def test_worldwide_counts_as_high_tier():
    """A worldwide posting is open to US/EU clients, so it can pay the high band."""
    assert high_tier_geography("Worldwide")


def test_dashboard_shows_one_band_when_geography_is_known():
    create_all(engine)
    client = TestClient(app)
    set_inbound_deps(DEPS)
    client.post("/run-inbound", json={"jobs": [
        {"source": "remotive", "title": "AI Engineer", "description": "agents", "location": "USA"}
    ]})

    r = client.get("/dashboard")
    assert "geography unknown" not in r.text.lower(), "we know where this client is"
    assert "USA" in r.text
