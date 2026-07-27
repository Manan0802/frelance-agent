"""Follow-up sequencing — the single biggest gap the conversion research found.

Measured evidence behind the design (Phase 13 research):
- Follow-ups carry **~42% of all replies**. Not having them leaves most of the
  return on every pitch unclaimed.
- 3-5 step sequences reply at ~8.3%; 4-7 touches is the usual optimum.
- "Just checking in" notes underperform substantive follow-ups by **15x** on
  meetings booked — so a follow-up has to say something new, not nudge.

Scheduling is deliberately a pure function over (sent_at, now): no clock inside
the logic, no background job needed, and the daily run can simply ask what's due.
"""

from datetime import datetime, timedelta

from backend.crm.followups import (
    FOLLOW_UP_DAYS, due_followups, next_step_for, is_sequence_finished,
)


class Rec:
    """Stand-in for a CrmRecord: what was sent, when, and how far along."""

    def __init__(self, sent_at, followups_sent=0, status="sent", id="r1"):
        self.id = id
        self.sent_at = sent_at
        self.followups_sent = followups_sent
        self.status = status
        self.message_id = "m1"
        self.target_name = "Acme"


NOW = datetime(2026, 8, 1, 12, 0)


def _sent_days_ago(n, **kw):
    return Rec(sent_at=NOW - timedelta(days=n), **kw)


def test_nothing_is_due_before_the_first_interval():
    assert due_followups([_sent_days_ago(1)], now=NOW) == []


def test_first_follow_up_becomes_due_on_schedule():
    due = due_followups([_sent_days_ago(FOLLOW_UP_DAYS[0])], now=NOW)
    assert [step for _rec, step in due] == [1]


def test_later_steps_wait_for_their_own_interval():
    """Day counts are measured from the original send, so a record already one
    step in shouldn't fire again until the next interval passes."""
    rec = _sent_days_ago(FOLLOW_UP_DAYS[0], followups_sent=1)
    assert due_followups([rec], now=NOW) == []

    rec = _sent_days_ago(FOLLOW_UP_DAYS[1], followups_sent=1)
    assert [step for _r, step in due_followups([rec], now=NOW)] == [2]


def test_a_long_overdue_lead_only_gets_its_next_step_not_a_burst():
    """Someone sent 90 days ago and never followed up must not receive four
    emails at once."""
    rec = _sent_days_ago(90, followups_sent=0)
    due = due_followups([rec], now=NOW)
    assert [step for _r, step in due] == [1]


def test_the_sequence_stops_after_the_last_step():
    rec = _sent_days_ago(365, followups_sent=len(FOLLOW_UP_DAYS))
    assert due_followups([rec], now=NOW) == []
    assert is_sequence_finished(rec)


def test_a_replied_lead_is_dropped_from_the_sequence():
    """Chasing someone who already answered is the worst possible touch."""
    rec = _sent_days_ago(30, status="replied")
    assert due_followups([rec], now=NOW) == []


def test_won_and_lost_leads_are_dropped_too():
    for status in ("won", "lost", "unsubscribed"):
        rec = _sent_days_ago(30, status=status)
        assert due_followups([rec], now=NOW) == [], status


def test_a_message_never_actually_sent_is_not_followed_up():
    """Approved but not yet sent — following up on a message the client never
    received would be incoherent."""
    assert due_followups([Rec(sent_at=None)], now=NOW) == []


def test_sequence_length_matches_the_researched_optimum():
    assert 3 <= len(FOLLOW_UP_DAYS) <= 7


def test_intervals_widen_rather_than_repeating_daily():
    assert FOLLOW_UP_DAYS == sorted(FOLLOW_UP_DAYS)
    gaps = [b - a for a, b in zip(FOLLOW_UP_DAYS, FOLLOW_UP_DAYS[1:])]
    assert gaps == sorted(gaps), "each gap should be at least as long as the last"


def test_next_step_reports_where_a_lead_is_in_the_sequence():
    assert next_step_for(_sent_days_ago(0)) == 1
    assert next_step_for(_sent_days_ago(0, followups_sent=2)) == 3
    assert next_step_for(_sent_days_ago(0, followups_sent=len(FOLLOW_UP_DAYS))) is None


def test_many_leads_are_triaged_in_one_pass():
    recs = [
        _sent_days_ago(1, id="too-soon"),
        _sent_days_ago(FOLLOW_UP_DAYS[0], id="due-1"),
        _sent_days_ago(FOLLOW_UP_DAYS[1], followups_sent=1, id="due-2"),
        _sent_days_ago(30, status="replied", id="replied"),
    ]
    due = due_followups(recs, now=NOW)
    assert {r.id for r, _ in due} == {"due-1", "due-2"}
