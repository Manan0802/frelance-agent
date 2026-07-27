"""Follow-up content.

The research is blunt about this: "just checking in" notes underperform
substantive follow-ups by **15x** on meetings booked. So each step has to carry
something the previous message didn't — a different angle, a concrete idea, a
smaller ask — and it must not repeat the original pitch back at them.

Same grounding rules as the first message apply: no invented business details,
no tech that isn't in the cited project's stack, no price.
"""

from backend.crm.followup_writer import write_followup, STEP_ANGLES
from backend.portfolio.context import PortfolioProject


class T:
    name = "Austin Dental"
    category = "dentist"
    location = "Austin, USA"
    website = None


PROJECTS = [PortfolioProject(name="SARA", type="ai_ml", description="agents", tech=["LangGraph"])]
ORIGINAL = "Hi — I couldn't find a website for Austin Dental. I'd automate your booking."


def _prompt_for(step, **kw):
    seen = {}

    def fake_llm(prompt):
        if "follow-up" in prompt.lower():
            seen["p"] = prompt
            return "draft"
        return "9"

    write_followup(T(), ORIGINAL, PROJECTS, step=step, llm=fake_llm, **kw)
    return seen["p"]


def test_every_scheduled_step_has_its_own_angle():
    from backend.crm.followups import FOLLOW_UP_DAYS

    assert len(STEP_ANGLES) == len(FOLLOW_UP_DAYS), "each step needs a distinct angle"
    assert len(set(STEP_ANGLES)) == len(STEP_ANGLES), "angles must not repeat"


def test_the_original_message_is_given_so_it_is_not_repeated():
    p = _prompt_for(1)
    assert ORIGINAL in p
    assert "repeat" in p.lower() or "restate" in p.lower()


def test_checking_in_style_nudges_are_forbidden():
    """Measured 15x worse than a substantive touch."""
    p = _prompt_for(1).lower()
    assert "checking in" in p, "the failure mode must be named explicitly"


def test_each_step_carries_a_different_instruction():
    prompts = [_prompt_for(s) for s in range(1, len(STEP_ANGLES) + 1)]
    assert len(set(prompts)) == len(prompts)


def test_the_last_step_closes_the_loop_rather_than_nagging():
    from backend.crm.followups import FOLLOW_UP_DAYS

    last = _prompt_for(len(FOLLOW_UP_DAYS)).lower()
    assert "last" in last or "final" in last or "close" in last


def test_grounding_rules_survive_into_follow_ups():
    """A follow-up is still a cold message — the anti-hallucination rules that
    took three phases to get right must not be dropped here."""
    p = _prompt_for(1)
    assert "LangGraph" in p, "cited project's real stack must reach the model"
    assert "invent" in p.lower()
    assert "price" in p.lower()


def test_follow_ups_get_a_word_RANGE_not_just_a_cap():
    """A bare "under 70 words" cap produced 11-word telegrams live — "Let's
    automate order tracking with Python. Would you like to explore this?" — which
    reads as low-effort. A floor keeps there being an actual message."""
    p = _prompt_for(1).lower()
    assert "40" in p and "70 words" in p


def test_no_website_follow_ups_are_scored_on_offer_not_tailoring():
    """Phase 7 split the rubrics because scoring a no-website pitch on tailoring
    floors it — there is nothing real to be specific about. write_followup
    inherited _score's has_source=True default and scored live follow-ups 0.0
    and 2.0 for exactly that reason."""
    seen = []

    def fake_llm(prompt):
        if "follow-up" in prompt.lower():
            return "draft"
        seen.append(prompt)
        return "8"

    write_followup(T(), ORIGINAL, PROJECTS, step=1, has_source=False, llm=fake_llm)
    assert "OFFER" in seen[0], "should use the offer-strength rubric"


def test_researched_follow_ups_still_use_the_tailoring_rubric():
    seen = []

    def fake_llm(prompt):
        if "follow-up" in prompt.lower():
            return "draft"
        seen.append(prompt)
        return "8"

    write_followup(T(), ORIGINAL, PROJECTS, step=1, has_source=True, llm=fake_llm)
    assert "tailored" in seen[0].lower()


def test_output_shape_matches_the_writers():
    out = write_followup(T(), ORIGINAL, PROJECTS, step=1,
                         llm=lambda p: "draft" if "follow-up" in p.lower() else "8")
    assert out["draft_text"] == "draft"
    assert out["personalization_score"] == 8.0
    assert out["portfolio_used"] == ["SARA"]
    assert out["step"] == 1


def test_an_out_of_range_step_is_rejected_rather_than_guessed():
    try:
        write_followup(T(), ORIGINAL, PROJECTS, step=99, llm=lambda p: "x")
    except ValueError:
        return
    raise AssertionError("step 99 should not silently produce a message")
