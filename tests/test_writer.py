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


def test_writer_returns_a_subject_so_the_email_is_actually_sendable():
    """The subject is generated from the final draft, not an intermediate one —
    a rewritten body with the first draft's subject is a mismatch the recipient
    sees before anything else."""
    projects = [PortfolioProject(name="Site", type="web", description="site")]
    research = {"research_summary": "s", "pain_points": "p", "has_source": True}

    def fake_llm(prompt):
        if "ONLY the subject line" in prompt:
            assert "final body" in prompt, "subject must be written from the final draft"
            return "Subject: your booking page"
        if "Write a" in prompt:
            return "final body — noticed you take bookings by phone."
        return "9"

    out = write_message(T(), research, projects, llm=fake_llm)
    assert out["subject"] == "your booking page"


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


def test_scorer_rubric_rejects_echoing_input_as_personalization():
    """A live run self-scored 8/10 for a message whose only "personalization"
    was restating the city we fed it ("I noticed you're based in Delhi").
    The rubric must state that echoing known facts doesn't count, otherwise
    the <7 regen gate never fires."""
    from backend.engine_b.writer import SCORE_PROMPT

    prompt = SCORE_PROMPT.format(msg="anything")
    lowered = prompt.lower()
    assert "restat" in lowered or "echo" in lowered, "must exclude echoed input"
    assert "generic" in lowered, "must name the generic-template failure mode"


def test_body_rules_follow_the_measured_cold_email_data():
    """From the cold-email skill's benchmark data: under 75 words earns 83% more
    replies (25-75 optimal), being self-focused is the #2 ranked mistake, and
    asking for a call in a first touch is "proposing on first date". The old
    120-word cap sat well above the useful range.

    The floor matters as much as the cap — a bare cap once produced 11-word
    telegrams (Phase 16).
    """
    from backend.engine_b.writer import RULES, NO_PROJECT_RULES

    for rules in (RULES, NO_PROJECT_RULES):
        assert "120 words" not in rules
        assert "75 words" in rules
        assert "40" in rules, "keep a floor, not a bare cap"
        assert "your" in rules.lower() and "I/we" in rules
        assert "call" in rules.lower()
