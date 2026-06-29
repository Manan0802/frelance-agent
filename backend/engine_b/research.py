import json

import httpx

from backend.llm.gemini import generate


def _default_fetch(url: str) -> str:
    try:
        r = httpx.get(
            url,
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": "FreelancingAgent/1.0"},
        )
        return r.text[:6000]
    except Exception:
        return ""


RESEARCH_PROMPT = """You are researching a local business for a freelance pitch.
Business: {name} ({category}) in {location}.
Website content (truncated):
{site}

Return ONLY JSON: {{"research_summary": "...", "pain_points": "concrete problems a web/AI dev could fix"}}"""


def research_target(target, fetch=_default_fetch, llm=generate) -> dict:
    site = fetch(target.website) if target.website else ""
    prompt = RESEARCH_PROMPT.format(
        name=target.name,
        category=target.category or "business",
        location=target.location or "",
        site=site or "(no website found)",
    )
    raw = llm(prompt)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"research_summary": raw.strip(), "pain_points": ""}
