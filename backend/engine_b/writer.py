from backend.llm.gemini import generate

RULES = """Rules: start with the client's problem (never "Hi I am Manan"); reference one
specific detail; mention one relevant past project; name the tech you'd use; under 120 words;
end with one question; do NOT commit a price; confident peer tone, not sycophantic."""

WRITE_PROMPT = """Write a cold outreach message to {name}, a {category} in {location}.
Their situation: {summary}
Their likely pain: {pain}
Relevant past work you can cite: {projects}
{rules}{stricter}"""

SCORE_PROMPT = """Rate this outreach message's personalization 0-10 (how specific to THIS
business vs generic). Reply with ONLY a number.

Message:
{msg}"""


def _draft(target, research, projects, llm, stricter=""):
    proj_str = "; ".join(f"{p.name}: {p.description}" for p in projects)
    return llm(
        WRITE_PROMPT.format(
            name=target.name,
            category=target.category or "business",
            location=target.location or "",
            summary=research.get("research_summary", ""),
            pain=research.get("pain_points", ""),
            projects=proj_str,
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
