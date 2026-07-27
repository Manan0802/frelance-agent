"""Batch approve — Manan's chosen middle path.

He picked "one click approves 20" over full auto-send. The point is that
everything up to the send runs unattended, and his part collapses to a single
action: ~30 seconds a day, while still putting human eyes on the copy before a
client sees it.

Six phases of live bugs (invented tech stacks, fabricated business details,
stretched portfolio matches) were all caught by a human reading output, which is
what this preserves.
"""

from fastapi.testclient import TestClient

from backend.database.connection import engine, SessionLocal
from backend.database.models import create_all, OutreachMessage, CrmRecord
from backend.main import app


def _draft(i, score=8.0, status="draft"):
    return OutreachMessage(id=f"m{i}", target_id=f"t{i}", draft_text=f"draft {i}",
                           personalization_score=score, status=status)


def _seed(*messages):
    create_all(engine)
    db = SessionLocal()
    for m in messages:
        db.add(m)
    db.commit()
    db.close()


def test_approves_every_pending_draft_in_one_call():
    _seed(_draft(1), _draft(2), _draft(3))
    r = TestClient(app).post("/dashboard/approve-all", json={})
    assert r.status_code == 200
    assert r.json()["approved"] == 3

    db = SessionLocal()
    assert db.query(OutreachMessage).filter_by(status="approved").count() == 3
    db.close()


def test_already_approved_drafts_are_not_touched_again():
    """Otherwise a second click doubles the CRM records."""
    _seed(_draft(1, status="approved"), _draft(2))
    r = TestClient(app).post("/dashboard/approve-all", json={})
    assert r.json()["approved"] == 1

    db = SessionLocal()
    assert db.query(CrmRecord).count() == 1
    db.close()


def test_a_minimum_score_can_be_required():
    """Bulk-approving weak drafts is the obvious way this goes wrong."""
    _seed(_draft(1, score=9.0), _draft(2, score=4.0), _draft(3, score=7.0))
    r = TestClient(app).post("/dashboard/approve-all", json={"min_score": 7})
    assert r.json()["approved"] == 2

    db = SessionLocal()
    assert db.query(OutreachMessage).filter_by(id="m2").first().status == "draft"
    db.close()


def test_a_batch_is_capped_so_one_click_cannot_approve_everything():
    _seed(*[_draft(i) for i in range(30)])
    r = TestClient(app).post("/dashboard/approve-all", json={"limit": 20})
    assert r.json()["approved"] == 20


def test_approving_nothing_is_not_an_error():
    _seed()
    r = TestClient(app).post("/dashboard/approve-all", json={})
    assert r.status_code == 200 and r.json()["approved"] == 0


def test_approval_still_does_not_send_anything():
    """Approve marks ready. Sending stays a separate, deliberate step."""
    _seed(_draft(1))
    r = TestClient(app).post("/dashboard/approve-all", json={})
    assert r.json()["sent"] == 0
