from backend.portfolio.context import PortfolioProject
from backend.engine_a.proposal import write_proposal


def test_proposal_regens_when_low_score():
    job = {"title": "LangGraph dev", "description": "build RAG agents"}
    projects = [PortfolioProject(name="SARA", type="ai", description="LangGraph multi-agent system")]
    state = {"drafts": 0}

    def fake_llm(prompt):
        if "Write a proposal" in prompt:
            state["drafts"] += 1
            return f"draft#{state['drafts']} I can build your RAG agents..."
        return "9" if "draft#2" in prompt else "3"

    out = write_proposal(job, projects, llm=fake_llm)
    assert out["personalization_score"] == 9.0
    assert state["drafts"] == 2
    assert "draft#2" in out["draft_text"]
    assert out["portfolio_used"] == ["SARA"]
