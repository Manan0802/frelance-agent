from backend.database.connection import engine, SessionLocal
from backend.database.models import create_all, OutboundTarget, OutreachMessage
from backend.portfolio.context import PortfolioContext, PortfolioProject
from backend.engine_b.graph import run_engine_b


def test_run_engine_b_persists_and_notifies():
    create_all(engine)
    db = SessionLocal()
    t = OutboundTarget(id="g1", name="Acme", dedup_hash="gh1", raw="{}")
    db.add(t)
    db.commit()
    pf = PortfolioContext(
        personal={"name": "Manan"},
        projects=[PortfolioProject(name="Site", type="web", description="website")],
    )
    sent = {}
    deps = {
        "research": lambda target: {"research_summary": "x", "pain_points": "no site"},
        "match": lambda need, projects: projects[:1],
        "write": lambda target, research, projects: {
            "draft_text": "Hi Acme",
            "personalization_score": 8.0,
            "portfolio_used": ["Site"],
        },
        "notify": lambda text: sent.update({"text": text}) or True,
    }
    out = run_engine_b([t], db, pf, deps=deps)
    assert len(out) == 1
    assert db.query(OutreachMessage).filter_by(target_id="g1").count() == 1
    assert "Acme" in sent["text"]
    db.close()
