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
- 3 to 7 words. Lowercase unless a real name needs a capital.
- Say what the email is actually about, drawn from the body.
- No exclamation marks, no ALL CAPS, no "Re:" or "Fwd:".
- No hype words (unlock, boost, revolutionise, transform, supercharge).
- It must not read like a mass email.

Reply with ONLY the subject line."""

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
    # An empty subject reads as automated — worse than a plain one.
    return clean_subject(raw) or f"Quick question about {target.name}"
