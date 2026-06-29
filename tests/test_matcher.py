from backend.portfolio.context import PortfolioProject
from backend.engine_b.matcher import match_projects


def test_match_picks_relevant():
    projects = [
        PortfolioProject(name="SARA", type="ai", description="LangGraph multi-agent system", pitch_for=["AI agent", "automation"]),
        PortfolioProject(name="Site", type="web", description="business website", pitch_for=["website", "landing page"]),
    ]
    fake_embed = lambda texts: [[1.0, 0.0] if "website" in t.lower() else [0.0, 1.0] for t in texts]
    out = match_projects("need a business website", projects, top_k=1, embed=fake_embed)
    assert out[0].name == "Site"
