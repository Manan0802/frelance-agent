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


def test_writer_grounds_tech_claims_in_the_portfolio():
    """The LLM must be told which tech each project actually used, and told not
    to invent any — a live run once produced "using WordPress" for a project
    whose real stack is React/Node, because tech was never in the prompt."""
    projects = [
        PortfolioProject(
            name="Site",
            type="web",
            description="business website",
            tech=["React", "Node.js"],
            pitch_for=["website"],
        )
    ]
    research = {"research_summary": "Outdated site", "pain_points": "no online booking"}
    seen = {}

    def fake_llm(prompt):
        if "Write a" in prompt:
            seen["draft_prompt"] = prompt
            return "Hi, Acme Dental has no online booking..."
        return "9"

    write_message(T(), research, projects, llm=fake_llm)

    p = seen["draft_prompt"]
    assert "React" in p and "Node.js" in p, "actual tech stack must reach the LLM"
    assert "invent" in p.lower(), "prompt must forbid inventing tech"
