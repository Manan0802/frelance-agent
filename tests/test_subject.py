"""A cold email needs a subject line, and a bad one costs more than a bad body —
it decides whether the body is ever read.

Generated from the finished draft in its own call rather than folded into
WRITE_PROMPT: that prompt is tuned over several phases, and this project has
already learned that a late-added rule quietly overrides earlier ones.
"""

from backend.engine_b.subject import subject_for, clean_subject


class Target:
    name = "Riverside Dental"
    category = "dentist"
    location = "Austin, USA"


def test_uses_the_model_line():
    out = subject_for("Hi — noticed you book by phone only.", Target(),
                      llm=lambda p: "your phone booking")
    assert out == "your phone booking"


def test_the_draft_and_the_business_are_both_in_the_prompt():
    seen = {}

    def fake_llm(prompt):
        seen["p"] = prompt
        return "booking without the phone"

    subject_for("Noticed you book by phone.", Target(), llm=fake_llm)
    assert "Riverside Dental" in seen["p"]
    assert "Noticed you book by phone." in seen["p"]


def test_strips_the_label_the_model_keeps_adding():
    assert clean_subject('Subject: "your booking page"') == "your booking page"
    assert clean_subject("**Subject:** quick question") == "quick question"


def test_strips_hype_punctuation():
    """Exclamation marks and ALL CAPS are the two loudest spam signals in a
    subject line, and the model reaches for both unprompted."""
    assert clean_subject("Grow your revenue!!!") == "Grow your revenue"
    assert clean_subject("URGENT: read this") == "read this"


def test_refuses_the_fake_reply_trick():
    """"Re:" on a first-contact email is a deception, not a tactic."""
    assert clean_subject("Re: our conversation") == "our conversation"
    assert clean_subject("Fwd: your website") == "your website"


def test_takes_only_the_first_line():
    assert clean_subject("your booking page\n\nHi there, I noticed...") == "your booking page"


def test_asks_for_the_length_the_data_supports():
    """2-word subjects get 60% more opens than 5-word ones, and going from 2 to 4
    words costs 17.5% of replies (Lavender/Belkins, via the cold-email skill).
    The earlier 3-7 word instruction was guessed and sat above that whole range."""
    seen = {}
    subject_for("body", Target(), llm=lambda p: seen.setdefault("p", p) and "x")
    assert "2 to 4 words" in seen["p"]
    assert "7 words" not in seen["p"]


def test_forbids_the_things_that_measurably_lose_opens():
    """Numbers and percentages cost 46% of opens; salesy verbs 17.9%."""
    seen = {}
    subject_for("body", Target(), llm=lambda p: seen.setdefault("p", p) and "x")
    for rule in ("number", "colleague"):
        assert rule in seen["p"].lower(), rule


def test_the_fallback_carries_no_company_name():
    """A company or first name in the subject signals automation — 12% fewer
    replies. The old fallback led with the business name."""
    out = subject_for("body", Target(), llm=lambda p: "   ")
    assert "Riverside" not in out
    assert len(out.split()) <= 3
    assert out == out.lower()


def test_an_llm_failure_does_not_lose_the_draft():
    def boom(prompt):
        raise RuntimeError("rate limited")

    assert subject_for("body", Target(), llm=boom)
