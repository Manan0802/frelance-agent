from backend.llm.gemini import generate
from backend.engine_b.writer import _score, format_projects

RULES = """Rules: open with the client's problem (never "Hi I am Manan"); reference one
specific detail from the job; cite one relevant past project; name the tech you'd use — use
ONLY tech listed in that project's stack above, never invent a tool or framework that isn't
listed; under 150 words; end with one question; do NOT commit a price; confident peer tone."""

NO_PROJECT_RULES = """Rules: open with the client's problem (never "Hi I am Manan"); reference one
specific detail from the job; DO NOT cite any past project and DO NOT NAME ANY SPECIFIC TECH,
framework or tool — you have been given none; under 150 words; end with one question; do NOT
commit a price; confident peer tone."""

WRITE_PROMPT = """Write a proposal for this freelance job.
Title: {title}
Description: {description}
Relevant past work to cite: {projects}
{rules}{stricter}"""


def _draft(job, projects, llm, stricter=""):
    proj_str = format_projects(projects)
    return llm(
        WRITE_PROMPT.format(
            title=job.get("title", ""),
            description=job.get("description", ""),
            projects=proj_str,
            rules=RULES if projects else NO_PROJECT_RULES,
            stricter=stricter,
        )
    )


def write_proposal(job, projects, llm=generate) -> dict:
    draft = _draft(job, projects, llm)
    score = _score(draft, llm)
    if score < 7:
        draft = _draft(job, projects, llm,
                       stricter="\nBe stricter: cite a concrete detail unique to this job.")
        score = _score(draft, llm)
    return {
        "draft_text": draft,
        "personalization_score": score,
        "portfolio_used": [p.name for p in projects],
    }
