import hashlib
import json
import uuid

from backend.database.models import JobLead, InboundProposal
from backend.engine_a.scorer import score_job
from backend.engine_a.proposal import write_proposal
from backend.engine_b.matcher import match_projects
from backend.notify.whatsapp import format_digest, send_whatsapp

TOP_N = 10


def _hash(title: str, source: str) -> str:
    return hashlib.sha256(f"{title}|{source}".encode()).hexdigest()


def run_engine_a(job_dicts, db, portfolio, deps=None):
    deps = deps or {}
    score = deps.get("score", lambda job, pf: score_job(job, pf))
    match = deps.get("match", lambda need, projects: match_projects(need, projects))
    write = deps.get("write", lambda job, projects: write_proposal(job, projects))
    notify = deps.get("notify", lambda text: send_whatsapp(text))

    seen: set[str] = set()
    scored = []
    for job in job_dicts:
        h = _hash(job.get("title", ""), job.get("source", ""))
        if h in seen or db.query(JobLead).filter_by(dedup_hash=h).first():
            continue
        seen.add(h)
        s = score(job, portfolio)
        lead = JobLead(
            id=str(uuid.uuid4()), source=job.get("source", ""),
            title=job.get("title", ""), description=job.get("description", ""),
            url=job.get("url"), budget=job.get("budget"), dedup_hash=h,
            score=s["score"], skill_matched=",".join(s["skill_matched"]),
            auto_rejected=s["auto_rejected"], raw=json.dumps(job),
        )
        db.add(lead)
        if not s["auto_rejected"]:
            scored.append((lead, job))
    db.commit()

    scored.sort(key=lambda lj: lj[0].score, reverse=True)
    proposals, digest_rows = [], []
    for lead, job in scored[:TOP_N]:
        projects = match(f"{job.get('title','')} {job.get('description','')}", portfolio.projects)
        w = write(job, projects)
        prop = InboundProposal(
            id=str(uuid.uuid4()), job_id=lead.id,
            portfolio_used=",".join(w["portfolio_used"]),
            draft_text=w["draft_text"], personalization_score=w["personalization_score"],
        )
        db.add(prop)
        proposals.append(prop)
        digest_rows.append({"name": lead.title, "score": w["personalization_score"],
                            "draft_text": w["draft_text"]})
    db.commit()
    if digest_rows:
        notify(format_digest(digest_rows))
    return proposals
