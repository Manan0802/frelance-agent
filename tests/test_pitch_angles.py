"""Two pitch angles, because the two segments need different offers.

No-website businesses are a strong segment, not a weak one: "I searched and
couldn't find your site — I'll build it, plus SEO so you show up on Google" is
a concrete, honest offer built on the one thing we actually verified. What it
must NOT do is invent details about the business itself.

Businesses that DO have a site get the research-driven angle, and shouldn't be
pitched a website they already have.
"""

from backend.engine_b.writer import write_message
from backend.portfolio.context import PortfolioProject


class T:
    name = "Verma Mithai"
    category = "Sweet Shop"
    location = "Delhi"
    website = None


PROJECTS = [PortfolioProject(name="Site", type="web", description="site", tech=["React"])]


def _capture(research):
    seen = {}

    def fake_llm(prompt):
        if "Write a" in prompt or "outreach" in prompt.lower() and "Score" not in prompt:
            seen.setdefault("draft_prompt", prompt)
            return "draft"
        seen.setdefault("score_prompt", prompt)
        return "9"

    write_message(T(), research, PROJECTS, llm=fake_llm)
    return seen


def test_no_website_angle_uses_the_absence_as_the_hook():
    """Phase 14 correction: this used to assert an "offer to build a site + SEO
    bonus" framing. Manan's position is that a website is the cheapest thing he
    sells and anchoring on it caps the relationship — the missing site is
    EVIDENCE the business runs manually, and the offer should be the business
    outcome. The hook itself survives; the offer changed."""
    seen = _capture({"research_summary": "", "pain_points": "", "has_source": False})
    p = seen["draft_prompt"].lower()
    assert "could not find" in p or "couldn't find" in p, "must use the searched-and-found-nothing hook"
    assert "manual" in p, "the absence should be read as evidence of manual operations"


def test_no_website_angle_still_forbids_inventing_business_details():
    seen = _capture({"research_summary": "", "pain_points": "", "has_source": False})
    assert "invent" in seen["draft_prompt"].lower()


def test_researched_angle_does_not_pitch_a_website_they_already_have():
    seen = _capture({"research_summary": "real site", "pain_points": "slow", "has_source": True})
    p = seen["draft_prompt"].lower()
    assert "already has a website" in p
    assert "could not find" not in p and "couldn't find" not in p


def test_ungrounded_pitches_are_scored_on_offer_not_fabricated_specifics():
    """The strict personalization rubric would floor every no-website pitch at
    ~4/10 and regen pointlessly — there is nothing real to be specific about.
    Score those on how concrete the offer is instead."""
    seen = _capture({"research_summary": "", "pain_points": "", "has_source": False})
    assert "offer" in seen["score_prompt"].lower()
