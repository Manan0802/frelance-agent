"""Make the writing read like a person, not a model.

Manan's priority (2026-07-27): "proper humanize message chahiye". A pitch that
reads as machine-written gets deleted on sight — and every message here is
Gemini-written, so the tells have to be designed out rather than hoped away.

The tells below are the ones that actually appear in this project's own live
output, not a generic listicle: "leverage", "streamline", "I'd like to offer a
solution", "This would optimize...", "Can you afford to...".
"""

from backend.engine_b.humanize import ai_tells, sounds_human, HUMAN_RULES


def test_flags_corporate_filler_verbs():
    """Straight from live output: "Using Next.js, I can help leverage..." and
    "This would optimize your online presence"."""
    tells = ai_tells("I can leverage automation to streamline and optimize your workflow.")
    assert tells


def test_flags_the_rhetorical_scare_question():
    """"Can you afford to lose potential customers?" appeared in three separate
    live drafts. It's a telemarketer move and it reads as one."""
    assert ai_tells("Can you afford to lose potential customers due to slow loading?")


def test_flags_email_opener_boilerplate():
    for opener in ("I hope this email finds you well.",
                   "I hope you're doing well.",
                   "I wanted to reach out regarding your business."):
        assert ai_tells(opener), opener


def test_flags_the_not_just_x_but_y_construction():
    assert ai_tells("This isn't just a website, it's a growth engine.")


def test_flags_llm_favourite_adjectives():
    assert ai_tells("A seamless, robust solution to elevate your business.")


def test_flags_em_dash_pileups():
    """Models reach for em-dashes far more than people do."""
    assert ai_tells("Your booking — which is manual — costs time — and money.")


def test_flags_the_delve_family():
    assert ai_tells("Let's delve into how we can unlock your potential.")


def test_a_plainly_written_message_passes():
    plain = (
        "I looked for your site and couldn't find one. Most of the dentists I've "
        "worked with were still taking bookings by phone, which eats the front "
        "desk's day. I built a booking assistant that handles that. "
        "Worth a quick call?"
    )
    assert ai_tells(plain) == [], ai_tells(plain)
    assert sounds_human(plain)


def test_reports_which_tells_were_found_not_just_a_boolean():
    """The regen prompt needs to name the problem, or the model repeats it."""
    tells = ai_tells("I hope this email finds you well. Let's leverage synergy.")
    assert len(tells) >= 2
    assert all(isinstance(t, str) and t for t in tells)


def test_rules_name_the_specific_words_to_avoid():
    rules = HUMAN_RULES.lower()
    for word in ("leverage", "streamline", "seamless", "delve"):
        assert word in rules, f"{word} should be named explicitly"


def test_rules_ask_for_contractions_and_plain_words():
    rules = HUMAN_RULES.lower()
    assert "contraction" in rules or "i'd" in rules or "don't" in rules


def test_writer_prompt_carries_the_human_rules():
    from backend.engine_b.writer import write_message
    from backend.portfolio.context import PortfolioProject

    class T:
        name = "Austin Dental"; category = "dentist"; location = "Austin, USA"; website = None

    seen = {}

    def fake_llm(prompt):
        if "Write a" in prompt:
            seen.setdefault("p", prompt)
            return "I looked for your site and couldn't find one. Worth a quick call?"
        return "9"

    write_message(T(), {"research_summary": "s", "pain_points": "p", "has_source": False},
                  [PortfolioProject(name="SARA", type="ai_ml", description="agents")], llm=fake_llm)
    assert "leverage" in seen["p"].lower(), "the banned-word list must reach the model"


def test_a_robotic_draft_is_rewritten_with_the_tell_named():
    """Telling a model to "sound more human" without naming what it did produces
    the same text again, so the regen prompt quotes the specific tell."""
    from backend.engine_b.writer import write_message
    from backend.portfolio.context import PortfolioProject

    class T:
        name = "Austin Dental"; category = "dentist"; location = "Austin, USA"; website = None

    prompts, drafts = [], iter([
        "I hope this email finds you well. Let's leverage automation.",
        "I couldn't find your site. Most clinics I work with book by phone. Call?",
    ])

    def fake_llm(prompt):
        if "Write a" in prompt:
            prompts.append(prompt)
            return next(drafts)
        return "9"

    out = write_message(T(), {"research_summary": "s", "pain_points": "p", "has_source": False},
                        [PortfolioProject(name="SARA", type="ai_ml", description="agents")],
                        llm=fake_llm)

    assert len(prompts) == 2, "a draft full of tells should be rewritten"
    assert "leverage" in prompts[1].lower() or "boilerplate" in prompts[1].lower()
    assert ai_tells(out["draft_text"]) == []


def test_a_human_sounding_draft_is_not_rewritten():
    from backend.engine_b.writer import write_message
    from backend.portfolio.context import PortfolioProject

    class T:
        name = "Austin Dental"; category = "dentist"; location = "Austin, USA"; website = None

    calls = {"n": 0}

    def fake_llm(prompt):
        if "Write a" in prompt:
            calls["n"] += 1
            return "I couldn't find your site. Most clinics still book by phone. Worth a call?"
        return "9"

    write_message(T(), {"research_summary": "s", "pain_points": "p", "has_source": False},
                  [PortfolioProject(name="SARA", type="ai_ml", description="agents")], llm=fake_llm)
    assert calls["n"] == 1, "a clean draft costs no extra LLM call"
