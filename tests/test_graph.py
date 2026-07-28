from backend.database.connection import engine, SessionLocal
from backend.database.models import create_all, OutboundTarget, OutreachMessage
from backend.portfolio.context import PortfolioContext, PortfolioProject
from backend.engine_b.graph import run_engine_b


def test_run_engine_b_persists_and_notifies():
    create_all(engine)
    db = SessionLocal()
    t = OutboundTarget(id="g1", name="Acme", dedup_hash="gh1", raw="{}")
    db.add(t)
    db.commit()
    pf = PortfolioContext(
        personal={"name": "Manan"},
        projects=[PortfolioProject(name="Site", type="web", description="website")],
    )
    sent = {}
    deps = {
        "research": lambda target: {"research_summary": "x", "pain_points": "no site"},
        "match": lambda need, projects: projects[:1],
        "write": lambda target, research, projects: {
            "draft_text": "Hi Acme",
            "personalization_score": 8.0,
            "portfolio_used": ["Site"],
        },
        "notify": lambda text: sent.update({"text": text}) or True,
    }
    out = run_engine_b([t], db, pf, deps=deps)
    assert len(out) == 1
    assert db.query(OutreachMessage).filter_by(target_id="g1").count() == 1
    assert "Acme" in sent["text"]
    db.close()


def _deps(**over):
    base = {
        "research": lambda target: {"research_summary": "x", "pain_points": "p"},
        "match": lambda need, projects: projects[:1],
        "write": lambda target, research, projects: {
            "draft_text": "Hi", "personalization_score": 7.0, "portfolio_used": ["Site"],
        },
        "notify": lambda text: True,
    }
    base.update(over)
    return base


def _pf():
    return PortfolioContext(
        personal={"name": "Manan"},
        projects=[PortfolioProject(name="Site", type="web", description="website")],
    )


def test_run_stores_a_contact_so_the_draft_can_actually_be_sent():
    create_all(engine)
    db = SessionLocal()
    t = OutboundTarget(id="g2", name="Cafe", website="https://cafe.ie",
                       dedup_hash="gh2", raw="{}")
    db.add(t)
    db.commit()

    deps = _deps(find_contact=lambda url: {"email": "hi@cafe.ie", "contact_url": None})
    run_engine_b([t], db, _pf(), deps=deps)

    assert db.get(OutboundTarget, "g2").email == "hi@cafe.ie"
    db.close()


def test_a_contact_form_counts_as_a_channel():
    create_all(engine)
    db = SessionLocal()
    t = OutboundTarget(id="g3", name="Firm", website="https://firm.com",
                       dedup_hash="gh3", raw="{}")
    db.add(t)
    db.commit()

    deps = _deps(find_contact=lambda url: {"email": None,
                                           "contact_url": "https://firm.com/contact"})
    run_engine_b([t], db, _pf(), deps=deps)

    assert db.get(OutboundTarget, "g3").contact_url == "https://firm.com/contact"
    db.close()


def test_no_lookup_when_there_is_nothing_to_look_up_or_it_is_already_known():
    """Two HTTP calls per target is the cost here — don't pay it for a target
    with no site, or one Overpass already gave an address for."""
    create_all(engine)
    db = SessionLocal()
    no_site = OutboundTarget(id="g4", name="Dentist", dedup_hash="gh4", raw="{}")
    known = OutboundTarget(id="g5", name="Shop", website="https://shop.com",
                           email="known@shop.com", dedup_hash="gh5", raw="{}")
    db.add_all([no_site, known])
    db.commit()

    calls = []
    deps = _deps(find_contact=lambda url: calls.append(url) or {"email": None,
                                                               "contact_url": None})
    run_engine_b([no_site, known], db, _pf(), deps=deps)

    assert calls == []
    db.close()
