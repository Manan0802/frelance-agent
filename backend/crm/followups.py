"""Follow-up sequencing.

The conversion research (Phase 13) put this as the biggest single gap: follow-ups
carry **~42% of all replies**, and the project had none — so most of the return
on every pitch was going unclaimed. 3-5 step sequences reply at ~8.3%, with 4-7
touches the usual optimum.

Scheduling is a pure function of (sent_at, followups_sent, now). No clock inside
the logic and no background job: the daily run asks what's due and gets an
answer it can act on.
"""

from datetime import datetime

# Days after the ORIGINAL send, not after the previous touch — measuring from
# one fixed point keeps the schedule stable if a step is skipped or delayed.
# Widening gaps: persistent early, unobtrusive later.
FOLLOW_UP_DAYS = [3, 7, 16, 30]

# A lead that has answered, closed, or opted out is out of the sequence.
# Chasing someone who already replied is the worst touch available.
CLOSED_STATUSES = {"replied", "won", "lost", "unsubscribed", "bounced"}


def next_step_for(record) -> int | None:
    """1-based index of the next follow-up, or None once the sequence is done."""
    sent = getattr(record, "followups_sent", 0) or 0
    return sent + 1 if sent < len(FOLLOW_UP_DAYS) else None


def is_sequence_finished(record) -> bool:
    return next_step_for(record) is None


def _is_due(record, now: datetime) -> int | None:
    if record.status in CLOSED_STATUSES:
        return None
    if not record.sent_at:
        return None  # never actually sent; nothing to follow up on
    step = next_step_for(record)
    if step is None:
        return None
    elapsed_days = (now - record.sent_at).total_seconds() / 86400
    return step if elapsed_days >= FOLLOW_UP_DAYS[step - 1] else None


def due_followups(records, now: datetime | None = None) -> list[tuple[object, int]]:
    """Records needing a follow-up right now, paired with which step it is.

    Returns at most ONE step per record: a lead left untouched for months should
    receive its next message, not four at once.
    """
    now = now or datetime.utcnow()
    out = []
    for record in records:
        step = _is_due(record, now)
        if step is not None:
            out.append((record, step))
    return out
