from backend.llm.gemini import generate
from backend.llm.parse import parse_json

REJECT_THRESHOLD = 40

SCORE_PROMPT = """Score this freelance job for a developer with these skills:
{skills}

Job title: {title}
Job description: {description}

Rate 0-100 how well it matches the developer's skills (100 = perfect fit).
Return ONLY JSON: {{"score": <int>, "skill_matched": ["<skill>", ...]}}"""


def _flatten_skills(portfolio) -> str:
    out = []
    for group in portfolio.skills.values():
        out.extend(group)
    return ", ".join(out)


def score_job(job: dict, portfolio, llm=generate) -> dict:
    prompt = SCORE_PROMPT.format(
        skills=_flatten_skills(portfolio),
        title=job.get("title", ""),
        description=job.get("description", ""),
    )
    data = parse_json(llm(prompt), {"score": 0, "skill_matched": []})
    score = float(data.get("score", 0))
    return {
        "score": score,
        "skill_matched": data.get("skill_matched", []),
        "auto_rejected": score < REJECT_THRESHOLD,
    }
