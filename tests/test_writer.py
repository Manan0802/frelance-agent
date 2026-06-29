from backend.portfolio.context import PortfolioProject
from backend.engine_b.writer import write_message


class T:
    name = "Acme Dental"
    category = "dentist"
    location = "Delhi"


def test_writer_regens_when_low_score():
    projects = [
        PortfolioProject(name="Site", type="web", description="business website", pitch_for=["website"])
    ]
    research = {"research_summary": "Outdated site", "pain_points": "no online booking"}
    state = {"drafts": 0}

    def fake_llm(prompt):
        if "Write a" in prompt:  # draft generation call
            state["drafts"] += 1
            return f"draft#{state['drafts']} Hi, Acme Dental has no online booking..."
        # scoring call: low score for draft#1, high score once draft#2 exists
        return "9" if "draft#2" in prompt else "4"

    out = write_message(T(), research, projects, llm=fake_llm)
    assert out["personalization_score"] == 9.0
    assert state["drafts"] == 2  # regenerated exactly once
    assert "Site" in out["portfolio_used"]
