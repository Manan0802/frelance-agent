"""Relevance floor on portfolio matching.

A live run pitched ShopLens (a visual *search* project, CLIP/FAISS) as a fix for
image *optimisation* — the matcher returned it simply because it was the least-bad
of five, and the writer papered over the gap.

Measured against the real portfolio with all-MiniLM-L6-v2, genuine matches score
0.38-0.74 while that stretch scored 0.189 — below even an unrelated legal query
(0.187). The bands don't overlap, so a floor between them removes stretches
without touching real matches.
"""

from backend.engine_b.matcher import match_projects, MIN_SIMILARITY
from backend.engine_b.writer import write_message
from backend.portfolio.context import PortfolioProject


class T:
    name = "Acme"
    category = "shop"
    location = "Delhi"
    website = None


def _projects():
    return [
        PortfolioProject(name="Site", type="web", description="business website", pitch_for=["website"]),
        PortfolioProject(name="SARA", type="ai_ml", description="LangGraph agents", pitch_for=["AI agent"]),
    ]


def _embed_with(scores):
    """Fake embedder placing the need at [1,0] and each project at a chosen cosine."""
    def embed(texts):
        out = [[1.0, 0.0]]
        for s in scores:
            out.append([s, (1 - s**2) ** 0.5])
        return out
    return embed


def test_drops_projects_below_the_relevance_floor():
    out = match_projects("need", _projects(), top_k=2, embed=_embed_with([0.9, 0.19]))
    assert [p.name for p in out] == ["Site"], "the 0.19 stretch must be dropped"


def test_keeps_all_genuinely_relevant_projects():
    out = match_projects("need", _projects(), top_k=2, embed=_embed_with([0.9, 0.5]))
    assert {p.name for p in out} == {"Site", "SARA"}


def test_returns_nothing_when_no_project_is_relevant():
    out = match_projects("need", _projects(), top_k=2, embed=_embed_with([0.1, 0.05]))
    assert out == []


def test_floor_admits_the_weakest_real_match_measured():
    """0.381 was the weakest genuine match measured (generic pain -> website);
    the floor must sit below it or real leads lose their citation."""
    assert MIN_SIMILARITY < 0.381
    assert MIN_SIMILARITY > 0.189, "must exclude the measured ShopLens stretch"


def test_writer_does_not_fabricate_a_citation_when_nothing_matched():
    """The floor can legitimately return zero projects. RULES still says "mention
    one relevant past project" — with an empty list the model would invent one,
    reintroducing exactly the hallucination class Phase 6 fixed."""
    seen = {}

    def fake_llm(prompt):
        if "Write a" in prompt:
            seen["p"] = prompt
            return "draft"
        return "9"

    write_message(T(), {"research_summary": "x", "pain_points": "y", "has_source": True}, [], llm=fake_llm)
    p = seen["p"].lower()
    assert "no past project" in p, "writer must be told there is no citable project"
    assert "do not cite" in p or "don't cite" in p, "and told not to invent one"


def test_writer_does_not_name_tech_when_no_project_grounds_it():
    """RULES orders the model to "name the tech you'd use — only tech listed in
    that project's stack". With no project there IS no listed stack, so the rule
    has nothing to draw on and the model fills the gap: a live run produced
    "Using Next.js, I can help" with no project cited. The no-match note must
    cancel the tech instruction too."""
    seen = {}

    def fake_llm(prompt):
        if "Write a" in prompt:
            seen["p"] = prompt
            return "draft"
        return "9"

    write_message(T(), {"research_summary": "x", "pain_points": "y", "has_source": True}, [], llm=fake_llm)
    assert "do not name any specific tech" in seen["p"].lower()
