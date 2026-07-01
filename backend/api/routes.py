import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.config import settings
from backend.database.connection import get_db
from backend.database.models import OutreachMessage, CrmRecord
from backend.engine_b.ingest import ingest_targets
from backend.engine_b.graph import run_engine_b
from backend.portfolio.context import load_portfolio

router = APIRouter()

MAX_TARGETS = 50  # cap per run: bounds LLM cost + WhatsApp volume

_RUN_DEPS: dict = {}


def set_run_deps(deps: dict) -> None:
    _RUN_DEPS.clear()
    _RUN_DEPS.update(deps)


def check_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """If settings.api_key is set, require it on state-changing calls.
    Unset (local dev) => no-op, endpoints stay open."""
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(401, "invalid or missing API key")


@router.post("/run")
def run(body: dict, db=Depends(get_db), _=Depends(check_api_key)):
    incoming = body.get("targets", [])
    if len(incoming) > MAX_TARGETS:
        raise HTTPException(400, f"too many targets (max {MAX_TARGETS})")
    targets = ingest_targets(incoming, db)
    pf = load_portfolio("data/portfolio_context.json")
    msgs = run_engine_b(targets, db, pf, deps=_RUN_DEPS or None)
    names = {t.id: t.name for t in targets}
    return {
        "messages": [
            {
                "id": m.id,
                "name": names.get(m.target_id, ""),
                "draft_text": m.draft_text,
                "score": m.personalization_score,
            }
            for m in msgs
        ]
    }


@router.get("/messages")
def list_messages(db=Depends(get_db)):
    return [
        {"id": m.id, "draft_text": m.draft_text, "status": m.status}
        for m in db.query(OutreachMessage).all()
    ]


@router.patch("/messages/{message_id}/approve")
def approve(message_id: str, db=Depends(get_db), _=Depends(check_api_key)):
    m = db.query(OutreachMessage).filter_by(id=message_id).first()
    if not m:
        raise HTTPException(404, "message not found")
    m.status = "approved"
    rec = CrmRecord(
        id=str(uuid.uuid4()),
        message_id=m.id,
        target_name="",
        status="approved",
        created_at=datetime.utcnow(),
    )
    db.add(rec)
    db.commit()
    return {"id": m.id, "status": m.status, "crm_id": rec.id}
