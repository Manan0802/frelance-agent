"""The subject line for an outbound draft.

Written from the finished draft, in its own call. Folding it into WRITE_PROMPT
would be one fewer call, but that prompt is tuned across several phases and a
late-added rule there has already been observed overriding earlier ones.

The cleanup is not defensive padding — every rule below is a shape the model
actually returned during this project: a "Subject:" label, exclamation marks,
an ALL-CAPS opener, and "Re:" faking a reply thread.
"""

import re

from backend.llm.gemini import generate

SUBJECT_PROMPT = """Write the subject line for this cold email.

Business: {name} ({category}) in {location}
Email body:
{draft}

Rules:
- 2 to 4 words. All lowercase.
- It should look like it came from a colleague, not a vendor: name the topic
  plainly ("new patients", "booking delays", "front desk time").
- Draw it from the body — the topic, not a pitch.
- No numbers and no percentages.
- No exclamation marks, no ALL CAPS, no "Re:" or "Fwd:".
- No salesy verbs (boost, increase, unlock, transform, supercharge, grow).
- Do not put the business's name in it.

Reply with ONLY the subject line."""

# Last resort when the model returns nothing. Generic, and the data says generic
# questions underperform specific ones — but an empty subject reads as automated
# and a salesy one is worse. Two lowercase words is the safe floor.
FALLBACK = "quick question"

LABEL_RE = re.compile(r"^\W*(subject|betreff|objet)\s*:\s*", re.I)
FAKE_THREAD_RE = re.compile(r"^\s*(re|fwd|fw)\s*:\s*", re.I)
SHOUTED_PREFIX_RE = re.compile(r"^[A-Z][A-Z\s]{2,}:\s*")


def clean_subject(raw: str) -> str:
    s = (raw or "").strip().splitlines()[0] if (raw or "").strip() else ""
    s = LABEL_RE.sub("", s.strip())
    s = FAKE_THREAD_RE.sub("", s)
    s = SHOUTED_PREFIX_RE.sub("", s)
    s = s.strip().strip('"').strip("'").strip("*").strip()
    return s.rstrip("!").strip()


def subject_for(draft: str, target, llm=generate) -> str:
    try:
        raw = llm(
            SUBJECT_PROMPT.format(
                name=target.name,
                category=getattr(target, "category", None) or "business",
                location=getattr(target, "location", None) or "",
                draft=draft,
            )
        )
    except Exception:
        raw = ""
    return clean_subject(raw) or FALLBACK
