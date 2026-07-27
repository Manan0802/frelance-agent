from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates

from backend.database.connection import get_db
from backend.database.models import OutboundTarget, OutreachMessage, JobLead, InboundProposal
from backend.api.routes import approve_message, approve_proposal
from backend.portfolio.context import load_portfolio
from backend.pricing.suggest import suggest_rate, high_tier_geography

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


def _proposal_view(p: InboundProposal, leads: dict, project_types: dict) -> dict:
    used = [n.strip() for n in (p.portfolio_used or "").split(",") if n.strip()]
    is_agentic = any(project_types.get(n) == "ai_ml" for n in used)
    lead = leads.get(p.job_id)
    location = (lead.location if lead else "") or ""
    view = {
        "id": p.id,
        "name": lead.title if lead else "(unknown job)",
        "score": p.personalization_score,
        "status": p.status,
        "draft_text": p.draft_text,
        "created_at": p.created_at,
        "location": location,
        "high_tier": high_tier_geography(location),
    }
    if location:
        view["pricing"] = suggest_rate(is_agentic=is_agentic, client_geography=location)
    else:
        # Sources like the HN thread carry no location. Show both bands rather
        # than silently defaulting to the lower one, which would under-price
        # the international remote work these boards mostly carry.
        view["pricing_high"] = suggest_rate(is_agentic=is_agentic, client_geography="US")
        view["pricing_other"] = suggest_rate(is_agentic=is_agentic, client_geography="")
    return view


def _dashboard_context(db) -> dict:
    targets = db.query(OutboundTarget).all()
    leads = db.query(JobLead).all()
    targets_by_id = {t.id: t for t in targets}
    leads_by_id = {l.id: l for l in leads}
    project_types = _project_types()

    messages = (
        db.query(OutreachMessage).order_by(OutreachMessage.created_at.desc()).all()
    )
    proposals = (
        db.query(InboundProposal).order_by(InboundProposal.created_at.desc()).all()
    )

    message_views = [_message_view(m, targets_by_id, project_types) for m in messages]
    proposal_views = [_proposal_view(p, leads_by_id, project_types) for p in proposals]

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


@router.post("/dashboard/approve-all")
def approve_all(body: dict, db=Depends(get_db)):
    """Manan's chosen middle path: everything up to the send runs unattended,
    and his part is one action instead of twenty.

    Approving marks a draft ready — it sends nothing. Six phases of live bugs
    (invented tech, fabricated details, stretched matches) were all caught by a
    human reading output, which is what this preserves.
    """
    min_score = float(body.get("min_score") or 0)
    limit = int(body.get("limit") or 50)

    pending = (
        db.query(OutreachMessage)
        .filter(OutreachMessage.status == "draft")
        .filter(OutreachMessage.personalization_score >= min_score)
        .order_by(OutreachMessage.personalization_score.desc())
        .limit(limit)
        .all()
    )
    for message in pending:
        approve_message(db, message.id)
    return {"approved": len(pending), "sent": 0}


@router.patch("/dashboard/proposals/{proposal_id}/approve")
def dashboard_approve_proposal(proposal_id: str, request: Request, db=Depends(get_db)):
    p = approve_proposal(db, proposal_id)
    if not p:
        raise HTTPException(404, "proposal not found")
    leads_by_id = {l.id: l for l in db.query(JobLead).all()}
    return templates.TemplateResponse(
        request, "partials/proposal_row.html", {"p": _proposal_view(p, leads_by_id, _project_types())}
    )
