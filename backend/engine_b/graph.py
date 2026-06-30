import uuid

from backend.database.models import OutreachMessage
from backend.engine_b.research import research_target
from backend.engine_b.matcher import match_projects
from backend.engine_b.writer import write_message
from backend.notify.whatsapp import format_digest, send_whatsapp


def run_engine_b(targets, db, portfolio, deps=None):
    deps = deps or {}
    research = deps.get("research", lambda t: research_target(t))
    match = deps.get("match", lambda need, projects: match_projects(need, projects))
    write = deps.get("write", lambda t, r, p: write_message(t, r, p))
    notify = deps.get("notify", lambda text: send_whatsapp(text))

    messages, digest_rows = [], []
    for target in targets:
        r = research(target)
        projects = match(r.get("pain_points") or target.name, portfolio.projects)
        w = write(target, r, projects)
        msg = OutreachMessage(
            id=str(uuid.uuid4()),
            target_id=target.id,
            research_summary=r.get("research_summary", ""),
            pain_points=r.get("pain_points", ""),
            portfolio_used=",".join(w["portfolio_used"]),
            draft_text=w["draft_text"],
            personalization_score=w["personalization_score"],
        )
        db.add(msg)
        messages.append(msg)
        digest_rows.append(
            {
                "name": target.name,
                "score": w["personalization_score"],
                "draft_text": w["draft_text"],
            }
        )
    db.commit()
    if digest_rows:
        notify(format_digest(digest_rows))
    return messages
