"""Follow-up content.

The research is blunt: "just checking in" notes underperform substantive
follow-ups by **15x** on meetings booked. So each step carries a different
angle and something the previous message didn't say — and the original is
passed in so the model can avoid restating it.

The grounding rules that took three phases to get right (Phases 6-8) apply
unchanged here. A follow-up is still a cold message: no invented business
detail, no tech outside the cited project's stack, no price.
"""

from backend.llm.gemini import generate
from backend.engine_b.writer import _score, format_projects, NO_MATCH_NOTE
from backend.crm.followups import FOLLOW_UP_DAYS

# One angle per scheduled step, each giving the reader a reason to read that
# isn't "did you see my email".
STEP_ANGLES = [
    "Offer a single concrete idea for their business that the first message "
    "didn't mention — one specific thing you'd build or automate first, and why "
    "that one.",

    "Shift the frame to proof: reference the past project you cited and what it "
    "actually achieved, so they can judge the work rather than the claim.",

    "Make the ask smaller. Instead of proposing the project, offer a short call "
    "or a quick look at their setup — something that costs them almost nothing.",

    "Close the loop politely: say you'll stop reaching out, leave the offer open, "
    "and make it easy to reply later. No guilt, no final-notice pressure.",
]

# Length is a RANGE, not a cap. A bare "under 70 words" produced 10-18 word
# telegrams live ("Let's automate order tracking with LangGraph. Would that
# interest you?"), which read as low-effort. Note also that the rationale stays
# here in the comment: an earlier version explained itself inside the prompt,
# mentioning "11-word telegrams", and the model anchored on that number.
RULES = """Rules for this follow-up:
- Write 40 to 70 words. Fewer than 40 reads as a throwaway nudge; write in full
  sentences, not a one-line telegram.
- Do NOT restate or repeat the original message.
- Do NOT write a "just checking in" or "did you see my email" nudge — say
  something substantive instead.
- Name tech ONLY if it appears in the cited project's stack above, and never
  invent details about their business.
- Do NOT commit a price.
- End with one easy question. Confident peer tone."""

FOLLOW_UP_PROMPT = """Write follow-up number {step} to {name}, a {category} in {location}.

The original message you sent them was:
\"\"\"{original}\"\"\"

They have not replied.

Past work you can cite: {projects}

ANGLE FOR THIS FOLLOW-UP — {angle}

{rules}"""


def write_followup(target, original_message, projects, step: int,
                   has_source: bool = False, llm=generate) -> dict:
    """has_source mirrors the main writer: a no-website follow-up is judged on
    offer strength, not tailoring. Scoring it on tailoring floors it — live
    follow-ups came back 0.0 and 2.0 before this was threaded through."""
    if not 1 <= step <= len(FOLLOW_UP_DAYS):
        raise ValueError(f"step {step} is outside the {len(FOLLOW_UP_DAYS)}-step sequence")

    proj_str = format_projects(projects) if projects else NO_MATCH_NOTE
    draft = llm(
        FOLLOW_UP_PROMPT.format(
            step=step,
            name=target.name,
            category=getattr(target, "category", None) or "business",
            location=getattr(target, "location", None) or "",
            original=original_message,
            projects=proj_str,
            angle=STEP_ANGLES[step - 1],
            rules=RULES,
        )
    )
    return {
        "draft_text": draft,
        "personalization_score": _score(draft, llm, has_source),
        "portfolio_used": [p.name for p in projects],
        "step": step,
    }
