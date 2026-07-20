from backend.llm.gemini import generate

RULES = """Rules: start with the client's problem (never "Hi I am Manan"); reference one
specific detail; mention one relevant past project; name the tech you'd use — use ONLY tech
listed in that project's stack above, never invent a tool or framework that isn't listed;
under 120 words; end with one question; do NOT commit a price; confident peer tone, not
sycophantic."""

WRITE_PROMPT = """Write a cold outreach message to {name}, a {category} in {location}.
Their situation: {summary}
Their likely pain: {pain}
Relevant past work you can cite: {projects}
{grounding}{rules}{stricter}"""

UNGROUNDED_NOTE = """
IMPORTANT: there is NO VERIFIED information about this business — the notes above are inference
from its category alone. Do NOT invent or assert specifics (products they sell, their customers,
their history, what their current setup looks like). A believable-sounding guess that turns out
wrong loses the client. Lead with the offer instead, and keep it short.
"""

SCORE_PROMPT = """Score this cold outreach message 0-10 on how specifically it is tailored to
THIS business. Judge tailoring only — not how well written or persuasive it is.

Does NOT count as personalization:
- restating facts the sender already knew (the business name, its city, its category)
- generic claims any competitor could receive ("no online presence", "missing out on sales")
- flattery

Does count:
- a concrete detail that could only come from actually looking at this business
- a problem tied to how THIS business specifically operates

0-3 = generic template, could be sent to any business of this type.
4-6 = lightly tailored, but no real insight about them.
7-8 = one genuine specific observation about this business.
9-10 = multiple specific observations, tied to a concrete proposed fix.

Reply with ONLY a number.

Message:
{msg}"""


def format_projects(projects) -> str:
    """Include each project's real stack — without it the LLM has no grounding
    for the "name the tech you'd use" rule and invents one."""
    return "; ".join(
        f"{p.name} [built with: {', '.join(p.tech)}]: {p.description}" if p.tech
        else f"{p.name}: {p.description}"
        for p in projects
    )


def _draft(target, research, projects, llm, stricter=""):
    proj_str = format_projects(projects)
    return llm(
        WRITE_PROMPT.format(
            name=target.name,
            category=target.category or "business",
            location=target.location or "",
            summary=research.get("research_summary", ""),
            pain=research.get("pain_points", ""),
            projects=proj_str,
            grounding="" if research.get("has_source") else UNGROUNDED_NOTE,
            rules=RULES,
            stricter=stricter,
        )
    )


def _score(msg, llm) -> float:
    raw = llm(SCORE_PROMPT.format(msg=msg))
    try:
        return float("".join(c for c in raw if c.isdigit() or c == ".")[:4])
    except ValueError:
        return 0.0


def write_message(target, research, projects, llm=generate) -> dict:
    draft = _draft(target, research, projects, llm)
    score = _score(draft, llm)
    if score < 7:
        draft = _draft(
            target,
            research,
            projects,
            llm,
            stricter="\nBe stricter: cite a concrete detail unique to this business.",
        )
        score = _score(draft, llm)
    return {
        "draft_text": draft,
        "personalization_score": score,
        "portfolio_used": [p.name for p in projects],
    }
