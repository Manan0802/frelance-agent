from backend.database.connection import engine, SessionLocal
from backend.database.models import create_all, JobLead, InboundProposal
from backend.portfolio.context import PortfolioContext, PortfolioProject
from backend.engine_a.graph import run_engine_a


def test_run_engine_a_persists_and_notifies():
    create_all(engine)
    db = SessionLocal()
    pf = PortfolioContext(
        personal={"name": "Manan"},
        projects=[PortfolioProject(name="SARA", type="ai", description="LangGraph agents")],
    )
    jobs = [
        {"source": "remoteok", "title": "LangGraph dev", "description": "RAG"},
        {"source": "remoteok", "title": "Plumber", "description": "pipes"},
    ]
    sent = {}
    deps = {
        "score": lambda job, portfolio: {
            "score": 90 if "LangGraph" in job["title"] else 10,
            "skill_matched": ["LangGraph"] if "LangGraph" in job["title"] else [],
            "auto_rejected": "Plumber" in job["title"],
        },
        "match": lambda need, projects: projects[:1],
        "write": lambda job, projects: {
            "draft_text": "Hi",
            "personalization_score": 8.0,
            "portfolio_used": [p.name for p in projects],
        },
        "notify": lambda text: sent.update({"text": text}) or True,
    }
    out = run_engine_a(jobs, db, pf, deps=deps)
    assert len(out) == 1  # plumber rejected
    assert db.query(JobLead).filter_by(auto_rejected=False).count() == 1
    assert db.query(InboundProposal).count() == 1
    assert "LangGraph dev" in sent["text"]
    db.close()
