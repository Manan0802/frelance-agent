from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates

from backend.database.connection import get_db
from backend.database.models import OutboundTarget, OutreachMessage, JobLead, InboundProposal
from backend.api.routes import approve_message, approve_proposal
from backend.portfolio.context import load_portfolio
from backend.pricing.suggest import suggest_rate

router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _project_types() -> dict:
    pf = load_portfolio("data/portfolio_context.json")
    return {p.name: p.type for p in pf.projects}


def _message_view(m: OutreachMessage, targets_by_id: dict, project_types: dict) -> dict:
    target = targets_by_id.get(m.target_id)
    used = [n.strip() for n in (m.portfolio_used or "").split(",") if n.strip()]
    is_agentic = any(project_types.get(n) == "ai_ml" for n in used)
    pricing = suggest_rate(is_agentic=is_agentic, client_geography=target.location if target else "")
    return {
        "id": m.id,
        "name": target.name if target else "(unknown target)",
        "score": m.personalization_score,
        "status": m.status,
        "draft_text": m.draft_text,
        "created_at": m.created_at,
        "pricing": pricing,
    }


def _proposal_view(p: InboundProposal, lead_titles: dict) -> dict:
    return {
        "id": p.id,
        "name": lead_titles.get(p.job_id, "(unknown job)"),
        "score": p.personalization_score,
        "status": p.status,
        "draft_text": p.draft_text,
        "created_at": p.created_at,
    }


def _dashboard_context(db) -> dict:
    targets = db.query(OutboundTarget).all()
    leads = db.query(JobLead).all()
    targets_by_id = {t.id: t for t in targets}
    lead_titles = {l.id: l.title for l in leads}
    project_types = _project_types()

    messages = (
        db.query(OutreachMessage).order_by(OutreachMessage.created_at.desc()).all()
    )
    proposals = (
        db.query(InboundProposal).order_by(InboundProposal.created_at.desc()).all()
    )

    message_views = [_message_view(m, targets_by_id, project_types) for m in messages]
    proposal_views = [_proposal_view(p, lead_titles) for p in proposals]

    return {
        "messages": message_views,
        "proposals": proposal_views,
        "stats": {
            "targets": len(targets),
            "leads": len(leads),
            "messages_total": len(message_views),
            "messages_approved": sum(1 for m in message_views if m["status"] == "approved"),
            "proposals_total": len(proposal_views),
            "proposals_approved": sum(1 for p in proposal_views if p["status"] == "approved"),
        },
    }


@router.get("/dashboard")
def dashboard(request: Request, db=Depends(get_db)):
    ctx = _dashboard_context(db)
    return templates.TemplateResponse(request, "dashboard.html", ctx)


@router.patch("/dashboard/messages/{message_id}/approve")
def dashboard_approve_message(message_id: str, request: Request, db=Depends(get_db)):
    result = approve_message(db, message_id)
    if not result:
        raise HTTPException(404, "message not found")
    m, _rec = result
    targets_by_id = {t.id: t for t in db.query(OutboundTarget).all()}
    return templates.TemplateResponse(
        request, "partials/message_row.html", {"m": _message_view(m, targets_by_id, _project_types())}
    )


@router.patch("/dashboard/proposals/{proposal_id}/approve")
def dashboard_approve_proposal(proposal_id: str, request: Request, db=Depends(get_db)):
    p = approve_proposal(db, proposal_id)
    if not p:
        raise HTTPException(404, "proposal not found")
    lead_titles = {l.id: l.title for l in db.query(JobLead).all()}
    return templates.TemplateResponse(
        request, "partials/proposal_row.html", {"p": _proposal_view(p, lead_titles)}
    )
