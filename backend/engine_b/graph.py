import logging
import uuid

from backend.database.models import OutreachMessage
from backend.engine_b.contacts import find_contact
from backend.engine_b.research import research_target
from backend.engine_b.matcher import match_projects
from backend.engine_b.writer import write_message
from backend.notify.whatsapp import format_digest, send_whatsapp
from backend.compliance import with_compliance

log = logging.getLogger(__name__)


def run_engine_b(targets, db, portfolio, deps=None):
    deps = deps or {}
    research = deps.get("research", lambda t: research_target(t, portfolio=portfolio))
    match = deps.get("match", lambda need, projects: match_projects(need, projects))
    write = deps.get("write", lambda t, r, p: write_message(t, r, p))
    notify = deps.get("notify", lambda text: send_whatsapp(text))
    find = deps.get("find_contact", find_contact)

    messages, digest_rows = [], []
    for target in targets:
        # Nobody is watching cron. A live 25-target run died partway through on
        # a provider 429 and lost every draft before it, because the commit was
        # after the loop. One bad target must cost one draft, not the morning.
        try:
            # A draft with nowhere to send it isn't a lead. Its own fetch rather
            # than research's: research truncates at 6k chars and the address is
            # usually in the footer, well past that.
            if target.website and not target.email:
                c = find(target.website)
                target.email = c["email"]
                target.contact_url = c["contact_url"]
            r = research(target)
            projects = match(r.get("pain_points") or target.name, portfolio.projects)
            w = write(target, r, projects)
            # Applied to the STORED draft, not just in transit: the stored text
            # is what Manan reviews and sends, so the guard has to live here.
            w["draft_text"] = with_compliance(w["draft_text"], target.location or "")
            msg = OutreachMessage(
                id=str(uuid.uuid4()),
                target_id=target.id,
                research_summary=r.get("research_summary", ""),
                pain_points=r.get("pain_points", ""),
                portfolio_used=",".join(w["portfolio_used"]),
                subject=w.get("subject", ""),
                draft_text=w["draft_text"],
                personalization_score=w["personalization_score"],
            )
            db.add(msg)
            db.commit()
        except Exception:
            log.exception("engine B: %s failed, skipping", target.name)
            db.rollback()
            continue
        messages.append(msg)
        digest_rows.append(
            {
                "name": target.name,
                "score": w["personalization_score"],
                "draft_text": w["draft_text"],
            }
        )
    if digest_rows:
        notify(format_digest(digest_rows))
    return messages
