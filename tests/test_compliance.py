"""Compliance guards on outbound messages.

Two findings from the 2026-07-27 delivery research, both time-sensitive:

1. **EU AI Act Article 50 applies from August 2026** — a month away. AI-generated
   text interacting with a person requires a transparency disclosure. Every
   message here is model-written, and EU businesses are targeted, so EU-bound
   outreach carries a disclosure line.

   This is a conservative reading rather than settled case law, hence a
   deterministic append rather than a prompt instruction: an instruction the
   model can quietly drop is not a compliance control.

2. **Germany requires double opt-in even for B2B email.** ePrivacy is transposed
   per member state, and Germany's transposition makes cold B2B email
   impermissible — so German targets are flagged as not-emailable rather than
   being drafted for a channel that can't lawfully be used.
"""

from backend.config import settings
from backend.compliance import (
    needs_ai_disclosure, AI_DISCLOSURE, with_compliance, email_permitted,
)


def test_eu_targets_get_a_disclosure():
    for place in ("Berlin, Germany", "Paris, France", "Dublin, Ireland",
                  "Amsterdam, Netherlands", "Milan, Italy", "Madrid, Spain"):
        assert needs_ai_disclosure(place), place


def test_uk_is_covered_too():
    """The UK kept a GDPR/PECR regime post-Brexit; treat it the same way."""
    assert needs_ai_disclosure("London, UK")


def test_non_eu_targets_are_left_alone():
    for place in ("Austin, USA", "Toronto, Canada", "Sydney, Australia",
                  "New Delhi, India", "Singapore, Singapore"):
        assert not needs_ai_disclosure(place), place


def test_unknown_location_does_not_trigger_a_disclosure():
    """Appending a disclosure everywhere would be a needless credibility cost on
    messages that don't require one."""
    assert not needs_ai_disclosure("")


def test_disclosure_is_appended_to_eu_messages(monkeypatch):
    monkeypatch.setattr(settings, 'ai_disclosure_enabled', True)
    out = with_compliance("Hi, I noticed your booking is by phone.", "Berlin, Germany")
    assert out.startswith("Hi, I noticed your booking is by phone.")
    assert AI_DISCLOSURE in out


def test_disclosure_is_not_appended_twice(monkeypatch):
    monkeypatch.setattr(settings, 'ai_disclosure_enabled', True)
    once = with_compliance("Hello.", "Paris, France")
    twice = with_compliance(once, "Paris, France")
    assert twice.count(AI_DISCLOSURE) == 1


def test_non_eu_messages_are_returned_untouched():
    msg = "Hi, I couldn't find a website for your clinic."
    assert with_compliance(msg, "Austin, USA") == msg


def test_the_disclosure_is_short_and_plain():
    """It sits at the end of a 90-word cold email; a legal paragraph would
    swamp the message."""
    assert len(AI_DISCLOSURE.split()) <= 20


def test_germany_is_not_emailable():
    """German ePrivacy transposition requires double opt-in even B2B."""
    assert not email_permitted("Munich, Germany")
    assert not email_permitted("Berlin, Germany")


def test_other_markets_remain_emailable():
    for place in ("Austin, USA", "London, UK", "Paris, France", "Dublin, Ireland"):
        assert email_permitted(place), place


def test_unknown_location_is_emailable():
    """Absent evidence of a restriction, don't block the pipeline."""
    assert email_permitted("")


def test_engine_b_applies_compliance_to_stored_drafts(monkeypatch):
    monkeypatch.setattr(settings, 'ai_disclosure_enabled', True)
    """The guard has to sit in the pipeline, not just exist as a helper — the
    stored draft is what Manan reviews and sends."""
    from backend.database.connection import engine, SessionLocal
    from backend.database.models import create_all, OutreachMessage, OutboundTarget
    from backend.engine_b.graph import run_engine_b
    from backend.portfolio.context import PortfolioContext, PortfolioProject

    create_all(engine)
    db = SessionLocal()
    target = OutboundTarget(id="t-eu", name="Berlin Zahnarzt", location="Berlin, Germany",
                            dedup_hash="h-eu", raw="{}")
    db.add(target)
    db.commit()

    pf = PortfolioContext(personal={"name": "Manan"},
                          projects=[PortfolioProject(name="SARA", type="ai_ml", description="agents")])
    run_engine_b([target], db, pf, deps={
        "research": lambda t: {"research_summary": "s", "pain_points": "p", "has_source": False},
        "match": lambda need, projects: projects[:1],
        "write": lambda t, r, p: {"draft_text": "Guten Tag, ich baue Automatisierung.",
                                  "personalization_score": 8.0, "portfolio_used": ["SARA"]},
        "notify": lambda text: True,
    })

    stored = db.query(OutreachMessage).filter_by(target_id="t-eu").first()
    assert AI_DISCLOSURE in stored.draft_text
    db.close()


def test_engine_b_leaves_non_eu_drafts_unchanged():
    from backend.database.connection import engine, SessionLocal
    from backend.database.models import create_all, OutreachMessage, OutboundTarget
    from backend.engine_b.graph import run_engine_b
    from backend.portfolio.context import PortfolioContext, PortfolioProject

    create_all(engine)
    db = SessionLocal()
    target = OutboundTarget(id="t-us", name="Austin Dental", location="Austin, USA",
                            dedup_hash="h-us", raw="{}")
    db.add(target); db.commit()

    pf = PortfolioContext(personal={"name": "Manan"},
                          projects=[PortfolioProject(name="SARA", type="ai_ml", description="agents")])
    run_engine_b([target], db, pf, deps={
        "research": lambda t: {"research_summary": "s", "pain_points": "p", "has_source": False},
        "match": lambda need, projects: projects[:1],
        "write": lambda t, r, p: {"draft_text": "Hi there.", "personalization_score": 8.0,
                                  "portfolio_used": ["SARA"]},
        "notify": lambda text: True,
    })
    stored = db.query(OutreachMessage).filter_by(target_id="t-us").first()
    assert stored.draft_text == "Hi there."
    db.close()


def test_disclosure_is_off_by_default():
    """Manan's decision: no AI-disclosure line on his outbound. The machinery
    stays behind a flag rather than being deleted, so it's one setting away if
    he ever wants it."""
    assert settings.ai_disclosure_enabled is False
    msg = "Hallo, ich baue Automatisierung."
    assert with_compliance(msg, "Berlin, Germany") == msg
