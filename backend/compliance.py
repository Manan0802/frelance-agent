"""Compliance guards on outbound messages.

Two time-sensitive findings from the 2026-07-27 delivery research:

**EU AI Act Article 50 applies from August 2026** — next month. AI-generated
text interacting with a person requires a transparency disclosure. Every message
this system writes is model-generated and EU businesses are in scope, so
EU/UK-bound outreach carries a disclosure line.

It's appended deterministically rather than asked of the model: an instruction
the model can quietly drop is not a compliance control. This is a conservative
reading rather than settled case law — the cost of the line is a few words, the
cost of being wrong is regulatory.

**Germany requires double opt-in even for B2B email.** ePrivacy is transposed per
member state and Germany's transposition makes cold B2B email impermissible, so
German targets are marked not-emailable rather than being drafted for a channel
that can't lawfully be used. They remain valid phone/in-person targets.

None of this is legal advice; it is the conservative default. Worth a
professional's read before volume sending.
"""

import re

from backend.config import settings

AI_DISCLOSURE = "(This message was drafted with AI assistance.)"

# EU/EEA member states plus the UK, which kept a GDPR/PECR-equivalent regime.
_EU_UK = {
    "austria", "belgium", "bulgaria", "croatia", "cyprus", "czechia", "czech republic",
    "denmark", "estonia", "finland", "france", "germany", "greece", "hungary",
    "ireland", "italy", "latvia", "lithuania", "luxembourg", "malta", "netherlands",
    "poland", "portugal", "romania", "slovakia", "slovenia", "spain", "sweden",
    "iceland", "norway", "liechtenstein",
    "uk", "united kingdom", "britain", "england", "scotland", "wales",
    "eu", "europe", "eea",
}

# Cities, because a lead's location is often a bare city or street address
# rather than "City, Country" — the same gap that once mispriced a Delhi lead.
_EU_UK_CITIES = {
    "berlin", "munich", "hamburg", "frankfurt", "cologne", "stuttgart", "dusseldorf",
    "paris", "lyon", "marseille", "toulouse", "amsterdam", "rotterdam", "eindhoven",
    "brussels", "antwerp", "madrid", "barcelona", "valencia", "seville",
    "milan", "rome", "turin", "bologna", "lisbon", "porto", "vienna",
    "stockholm", "gothenburg", "copenhagen", "oslo", "helsinki",
    "warsaw", "krakow", "prague", "budapest", "bucharest", "athens", "sofia",
    "zagreb", "tallinn", "vilnius", "riga", "dublin", "cork",
    "london", "manchester", "birmingham", "leeds", "glasgow", "edinburgh",
    "bristol", "liverpool", "cardiff", "belfast",
}

# Markets where cold B2B email is not permissible under local transposition.
_NO_COLD_EMAIL = {"germany", "berlin", "munich", "hamburg", "frankfurt",
                  "cologne", "stuttgart", "dusseldorf"}


def _matcher(terms):
    return re.compile(
        r"\b(" + "|".join(sorted((re.escape(t) for t in terms), key=len, reverse=True)) + r")\b",
        re.I,
    )


_EU_MATCH = _matcher(_EU_UK | _EU_UK_CITIES)
_NO_EMAIL_MATCH = _matcher(_NO_COLD_EMAIL)


def needs_ai_disclosure(location: str) -> bool:
    return bool(_EU_MATCH.search(location or ""))


def email_permitted(location: str) -> bool:
    """False where cold B2B email isn't lawful. Unknown locations stay
    permitted — absent evidence of a restriction, don't block the pipeline."""
    return not _NO_EMAIL_MATCH.search(location or "")


def with_compliance(message: str, location: str) -> str:
    if not settings.ai_disclosure_enabled:
        return message
    if not needs_ai_disclosure(location) or AI_DISCLOSURE in message:
        return message
    return f"{message}\n\n{AI_DISCLOSURE}"
