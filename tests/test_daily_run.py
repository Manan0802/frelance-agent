"""The daily run — Engine B end to end, unattended.

Manan asked for Engine B to work on his behalf: find businesses, research them,
write the pitch, and have everything queued without him driving it. This is that
entrypoint, designed to be called by cron once a morning.

What it does NOT do is send. Nothing in this module reaches a client — drafts
land in the review queue. Sending is a separate, deliberate decision (see the
deliverability and legal constraints in BUILD_LOG Phase 13).

It rotates through cities so repeated runs don't re-pitch the same street, and
it is bounded: an unbounded run over 214 cities would cost hundreds of LLM calls
in one morning.
"""

from datetime import datetime, timedelta

from backend.automation.daily import run_daily, pick_areas_for_run


class FakeDb:
    def __init__(self):
        self.added, self.committed = [], 0

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed += 1

    def query(self, *a, **kw):
        raise AssertionError("unexpected query in this test")


def test_picks_a_bounded_slice_of_cities():
    """214 cities in one morning would be hundreds of LLM calls."""
    picked = pick_areas_for_run(day_index=0, per_run=3)
    assert len(picked) == 3


def test_consecutive_days_target_different_cities():
    """Otherwise the same street gets pitched every morning."""
    day0 = {label for label, _ in pick_areas_for_run(day_index=0, per_run=3)}
    day1 = {label for label, _ in pick_areas_for_run(day_index=1, per_run=3)}
    assert not (day0 & day1)


def test_rotation_wraps_around_rather_than_running_out():
    from backend.engine_b.areas import AREAS

    far_future = len(AREAS) * 5
    assert pick_areas_for_run(day_index=far_future, per_run=3)


def test_a_run_fetches_researches_and_queues_without_sending():
    sent = []
    fetched = []

    def fake_fetch(areas):
        fetched.append(areas)
        return [{"name": "Austin Dental", "address": "Austin", "category": "dentist",
                 "website": None, "phone": None, "email": None}]

    result = run_daily(
        db=FakeDb(),
        fetch=fake_fetch,
        ingest=lambda rows, db: [type("T", (), dict(id="t1", **rows[0]))()],
        run_engine=lambda targets, db, pf, deps=None: [type("M", (), {"id": "m1"})()],
        notify=lambda text: sent.append(text),
        day_index=0,
    )

    assert fetched, "must actually source businesses"
    assert result["targets"] == 1
    assert result["messages_drafted"] == 1
    assert result["sent_to_clients"] == 0, "the daily run must never contact a client"


def test_the_digest_goes_to_manan_not_to_leads():
    """The only outbound message a run may produce is the summary to Manan."""
    notified = []
    run_daily(
        db=FakeDb(),
        fetch=lambda areas: [{"name": "X", "address": "A", "category": "c",
                              "website": None, "phone": None, "email": None}],
        ingest=lambda rows, db: [type("T", (), {"id": "t1"})()],
        run_engine=lambda targets, db, pf, deps=None: [type("M", (), {"id": "m1"})()],
        notify=lambda text: notified.append(text),
        day_index=0,
    )
    assert len(notified) == 1
    assert "review" in notified[0].lower() or "draft" in notified[0].lower()


def test_a_source_failure_does_not_crash_the_morning_run():
    """Cron has nobody watching it. A dead Overpass mirror must not mean a
    silent, permanently broken daily job."""
    def exploding_fetch(areas):
        raise RuntimeError("all overpass mirrors failed")

    result = run_daily(
        db=FakeDb(),
        fetch=exploding_fetch,
        ingest=lambda rows, db: [],
        run_engine=lambda *a, **kw: [],
        notify=lambda text: None,
        day_index=0,
    )
    assert result["targets"] == 0
    assert result["error"], "the failure is reported, not swallowed silently"


def test_finding_nothing_new_is_reported_not_treated_as_failure():
    """Every business in a city may already be in the DB from a prior run."""
    result = run_daily(
        db=FakeDb(),
        fetch=lambda areas: [{"name": "X", "address": "A", "category": "c",
                              "website": None, "phone": None, "email": None}],
        ingest=lambda rows, db: [],   # all deduped away
        run_engine=lambda *a, **kw: [],
        notify=lambda text: None,
        day_index=0,
    )
    assert result["targets"] == 0
    assert not result["error"]


def test_targets_per_run_are_capped():
    """One city can return 480 businesses; each costs several LLM calls."""
    many = [{"name": f"B{i}", "address": "A", "category": "c",
             "website": None, "phone": None, "email": None} for i in range(500)]
    seen = {}

    def spy_ingest(rows, db):
        seen["n"] = len(rows)
        return []

    run_daily(db=FakeDb(), fetch=lambda areas: many, ingest=spy_ingest,
              run_engine=lambda *a, **kw: [], notify=lambda t: None, day_index=0,
              max_targets=25)
    assert seen["n"] == 25


def test_day_index_defaults_to_todays_date_so_cron_needs_no_state():
    a = pick_areas_for_run(per_run=2)
    b = pick_areas_for_run(day_index=(datetime.utcnow() - datetime(2026, 1, 1)).days, per_run=2)
    assert a == b


def test_daily_run_spends_its_budget_on_businesses_it_can_actually_reach():
    """Measured on Austin: half the website-having rows yield an email or a form,
    against 8% of the no-website rows yielding a phone. The cap is what makes the
    ordering matter — 40 targets taken in Overpass order is mostly unreachable."""
    from backend.automation.daily import run_daily

    rows = [
        {"name": "NoSite A", "dedup_hash": "a"},
        {"name": "HasSite B", "website": "https://b.com", "dedup_hash": "b"},
        {"name": "NoSite C", "dedup_hash": "c"},
        {"name": "HasSite D", "website": "https://d.com", "dedup_hash": "d"},
    ]
    ingested = []

    run_daily(
        db=None,
        fetch=lambda areas: rows,
        ingest=lambda r, db: ingested.extend(r) or [],
        run_engine=lambda t, db, pf: [],
        notify=lambda text: True,
        max_targets=2,
    )

    assert [r["name"] for r in ingested] == ["HasSite B", "HasSite D"]
