from backend.portfolio.context import PortfolioContext
from backend.engine_a.scorer import score_job


def _pf():
    return PortfolioContext(personal={"name": "Manan"}, skills={"ai_ml": ["LangGraph", "RAG"]})


def test_high_score_not_rejected():
    job = {"title": "LangGraph dev", "description": "build RAG agents"}
    out = score_job(job, _pf(), llm=lambda p: '{"score": 88, "skill_matched": ["LangGraph"]}')
    assert out["score"] == 88
    assert out["auto_rejected"] is False
    assert "LangGraph" in out["skill_matched"]


def test_low_score_rejected():
    job = {"title": "Plumbing", "description": "fix pipes"}
    out = score_job(job, _pf(), llm=lambda p: '{"score": 12, "skill_matched": []}')
    assert out["auto_rejected"] is True
