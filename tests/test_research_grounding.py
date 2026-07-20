"""Grounding: the system must distinguish "researched" from "guessed".

A live run against a business with no website produced a confident research
summary and a pitch citing "popular items like gulab jamun" — none of it from
any source. Nothing had been fetched; the model invented all of it. Client-facing
claims must never be fabricated, so the pipeline has to carry whether real source
data existed.
"""

from backend.engine_b.research import research_target
from backend.engine_b.writer import write_message
from backend.portfolio.context import PortfolioProject


class T:
    name = "Gupta Sweets"
    category = "Sweet Shop"
    location = "Lajpat Nagar, Delhi"
    website = None


def test_research_reports_no_source_when_nothing_fetched():
    out = research_target(T(), fetch=lambda url: "", llm=lambda p: '{"research_summary": "s", "pain_points": "p"}')
    assert out["has_source"] is False


def test_research_reports_source_when_site_content_fetched():
    target = T()
    target.website = "https://example.com"
    out = research_target(
        target,
        fetch=lambda url: "<html>We hand-make bengali sweets since 1974</html>",
        llm=lambda p: '{"research_summary": "s", "pain_points": "p"}',
    )
    assert out["has_source"] is True


def test_writer_forbids_specifics_when_research_is_ungrounded():
    projects = [PortfolioProject(name="Site", type="web", description="site", tech=["React"])]
    research = {"research_summary": "guessed", "pain_points": "guessed", "has_source": False}
    seen = {}

    def fake_llm(prompt):
        if "Write a" in prompt:
            seen["p"] = prompt
            return "draft"
        return "9"

    write_message(T(), research, projects, llm=fake_llm)
    assert "no verified" in seen["p"].lower(), "writer must be told the research is unverified"


def test_writer_allows_specifics_when_research_is_grounded():
    projects = [PortfolioProject(name="Site", type="web", description="site", tech=["React"])]
    research = {"research_summary": "real", "pain_points": "real", "has_source": True}
    seen = {}

    def fake_llm(prompt):
        if "Write a" in prompt:
            seen["p"] = prompt
            return "draft"
        return "9"

    write_message(T(), research, projects, llm=fake_llm)
    assert "no verified" not in seen["p"].lower()
