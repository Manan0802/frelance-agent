"""The product is AI/automation/software, not websites.

Manan's correction (2026-07-27): "hum sirf website nahi bana rahe — AI related
service, software solutions, aur jo bhi Claude Code se karwa sakte hain, wo sab
pitch karenge. Khali website se paisa nahi banega."

The no-website angle had drifted into exactly that: it told the model to
"offer to build one" plus an SEO bonus. A website is a commodity deliverable —
it anchors the conversation at the cheapest thing he can sell. The missing site
should be read as EVIDENCE that the business runs manually, and the offer
should be the outcome (automated booking, enquiry handling, intake), with a
site as one possible vehicle rather than the product.
"""

from backend.engine_b.writer import write_message, NO_WEBSITE_ANGLE, RESEARCHED_ANGLE
from backend.portfolio.context import PortfolioProject


class T:
    name = "Austin Dental"
    category = "dentist"
    location = "Austin, USA"
    website = None


PROJECTS = [PortfolioProject(name="SARA", type="ai_ml", description="agents", tech=["LangGraph"])]


def _draft_prompt(has_source):
    seen = {}

    def fake_llm(prompt):
        if "Write a" in prompt:
            seen.setdefault("p", prompt)
            return "draft"
        return "9"

    write_message(T(), {"research_summary": "s", "pain_points": "p", "has_source": has_source},
                  PROJECTS, llm=fake_llm)
    return seen["p"]


def test_no_website_angle_leads_with_the_work_not_a_website_build():
    """All-rounder: pitch whatever the portfolio supports and the business
    needs — AI, automation, software, data, apps — a site is one option among
    them, not the default."""
    p = _draft_prompt(has_source=False).lower()
    assert "automat" in p, "manual work is the opening this segment gives"
    assert "manual" in p
    assert "past work" in p or "capabilit" in p, "offer must be drawn from the portfolio"


def test_no_website_angle_does_not_anchor_on_building_a_site():
    """"I'll build you a website" prices the whole relationship as a commodity."""
    angle = NO_WEBSITE_ANGLE.lower()
    assert "offer to build one" not in angle
    assert "seo" not in angle, "SEO-bonus framing is commodity positioning"


def test_no_website_angle_still_uses_the_absence_as_the_verified_hook():
    """The missing site stays the honest opening — it's the one verified fact —
    it just becomes evidence of manual operations rather than the product."""
    p = _draft_prompt(has_source=False).lower()
    assert "could not find" in p or "couldn't find" in p


def test_no_website_angle_still_forbids_inventing_details():
    assert "do not invent" in NO_WEBSITE_ANGLE.lower()


def test_researched_angle_reaches_for_ai_and_software_not_web_tweaks():
    a = RESEARCHED_ANGLE.lower()
    assert "ai" in a and "automat" in a
    assert 'build them a website' in a, "must still refuse to sell a site they already have"


def test_offer_scoring_rewards_outcomes_over_deliverable_lists():
    from backend.engine_b.writer import OFFER_SCORE_PROMPT

    s = OFFER_SCORE_PROMPT.lower()
    assert "outcome" in s or "saves" in s or "time" in s
