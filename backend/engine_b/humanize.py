"""Make the writing read like a person, not a model.

Manan's priority: "proper humanize message chahiye". A pitch that reads as
machine-written gets deleted on sight, and every message here is Gemini-written.

The patterns below are the ones that actually showed up in this project's own
live drafts — "leverage", "This would optimize your online presence", "Can you
afford to lose potential customers" — not a generic listicle. Detection feeds
the regen loop, so a flagged draft gets rewritten with the specific tell named;
telling the model "sound more human" without naming what it did produces the
same text again.
"""

import re

# (label, pattern) — the label goes into the regen prompt, so it has to say
# something the model can act on.
_TELLS: list[tuple[str, re.Pattern]] = [
    ("corporate filler verbs (leverage / streamline / optimize / utilize / facilitate)",
     re.compile(r"\b(leverage|leveraging|streamline|streamlining|utilis|utiliz|"
                r"facilitat|optimiz|optimis)\w*\b", re.I)),

    ("LLM adjectives (seamless / robust / cutting-edge / elevate / unlock / empower)",
     re.compile(r"\b(seamless\w*|robust|cutting[- ]edge|state[- ]of[- ]the[- ]art|"
                r"elevat\w+|unlock\w*|empower\w*|transformative|innovative solutions?)\b", re.I)),

    ("the delve/dive family",
     re.compile(r"\b(delve|dive deep|deep dive|embark on|navigate the landscape)\b", re.I)),

    ("email boilerplate opener (hope this finds you well / wanted to reach out)",
     re.compile(r"\b(hope (this|you)\s+\w*\s*(email\s+)?(finds you well|are doing well|"
                r"'?re doing well)|wanted to reach out|reaching out to you|"
                r"i hope you'?re? (doing )?well)\b", re.I)),

    ('the rhetorical scare question ("can you afford to...")',
     re.compile(r"\bcan you afford to\b|\bare you (still )?(losing|missing out)\b|"
                r"\bdon'?t let .{0,30}(slip|pass) (you )?by\b", re.I)),

    ('the "not just X, it\'s Y" construction',
     re.compile(r"\b(is|it'?s|this is)n'?t just .{1,40},? (it'?s|but)\b", re.I)),

    ("stacked em-dashes (people rarely use more than one)",
     re.compile(r"—.*—")),

    ("padding connectives (furthermore / moreover / additionally / in today's landscape)",
     re.compile(r"\b(furthermore|moreover|additionally|in today'?s?\s+\w+\s+"
                r"(landscape|world|market)|it'?s worth noting)\b", re.I)),

    ("vague benefit-speak (drive growth / boost your presence / take it to the next level)",
     re.compile(r"\b(drive (growth|results|engagement)|boost your \w+|"
                r"next level|game[- ]chang\w+|maximiz\w+ your \w+)\b", re.I)),
]

HUMAN_RULES = """Write like a person emailing another person, not like marketing copy:
- Use contractions (I'd, don't, you're). Short words over long ones.
- Vary sentence length. One short sentence beats a balanced tricolon.
- Never write: leverage, streamline, optimize, utilize, seamless, robust,
  cutting-edge, elevate, unlock, empower, delve, furthermore, moreover.
- No "I hope this email finds you well", no "I wanted to reach out".
- No rhetorical scare questions ("can you afford to lose customers?").
- At most one em-dash in the whole message.
- Say the plain version of the thing. If a tradesman wouldn't say it out loud,
  don't write it."""


def ai_tells(text: str) -> list[str]:
    """Labels for every machine-writing pattern found. Empty means it reads human."""
    return [label for label, pattern in _TELLS if pattern.search(text or "")]


def sounds_human(text: str) -> bool:
    return not ai_tells(text)
