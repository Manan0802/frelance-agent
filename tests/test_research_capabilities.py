"""Research must hunt for problems THIS developer can actually solve.

RESEARCH_PROMPT asked for "problems a web/AI dev could fix" without ever being
told what Manan builds. On a real diagnostics-lab site it came back with "slow
page loading, image rendering optimisation" — generic web-perf issues matching
nothing in his portfolio, so the relevance floor correctly returned no project
and the pitch went out with no proof. He builds AI agents, automation, RAG and
full-stack products; the research step has to look for those openings.
"""

from backend.engine_b.research import research_target, capability_summary
from backend.portfolio.context import PortfolioContext, PortfolioProject


class T:
    name = "Zeta Labs"
    category = "Diagnostics Lab"
    location = "Delhi"
    website = "https://example.com"


PF = PortfolioContext(
    personal={"name": "Manan"},
    skills={"ai_ml": ["LangGraph", "RAG"], "full_stack": ["React.js"]},
    projects=[
        PortfolioProject(
            name="SARA", type="ai_ml", description="autonomous agent",
            tech=["LangGraph"], pitch_for=["AI agent", "workflow automation"],
        ),
        PortfolioProject(
            name="Site", type="full_stack", description="business website",
            tech=["React.js"], pitch_for=["website", "online booking"],
        ),
    ],
)


def _capture(portfolio):
    seen = {}

    def fake_llm(prompt):
        seen["p"] = prompt
        return '{"research_summary": "s", "pain_points": "p"}'

    research_target(T(), portfolio=portfolio, fetch=lambda u: "<html>site</html>", llm=fake_llm)
    return seen["p"]


def test_capability_summary_lists_what_he_can_build():
    s = capability_summary(PF).lower()
    assert "ai agent" in s and "workflow automation" in s
    assert "online booking" in s


def test_research_prompt_carries_capabilities():
    p = _capture(PF).lower()
    assert "ai agent" in p, "research must know he builds AI agents"
    assert "workflow automation" in p


def test_research_asks_for_problems_in_those_areas_only():
    p = _capture(PF).lower()
    assert "only" in p or "prioritise" in p or "prioritize" in p


def test_research_still_works_without_a_portfolio():
    """Callers that don't pass a portfolio must not break."""
    out = research_target(
        T(), fetch=lambda u: "<html>x</html>",
        llm=lambda p: '{"research_summary": "s", "pain_points": "p"}',
    )
    assert out["pain_points"] == "p"
    assert out["has_source"] is True
