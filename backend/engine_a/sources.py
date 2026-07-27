"""Fan-in for Engine A's job sources.

Ordered freelance-first per project scope: the HN freelancer thread is real
project work, the remote job boards are mostly full-time employment and are
kept only for their contract/freelance slice.

A source that breaks (network, API change, rate limit) is logged and skipped —
one dead board must not take the morning's run down with it.
"""

import logging
import re

from backend.engine_a.hn_source import fetch_hn_freelance
from backend.engine_a.remoteok import fetch_remoteok
from backend.engine_a.weworkremotely import fetch_wwr

log = logging.getLogger(__name__)

DEFAULT_TAGS = ["python", "ai", "machine-learning", "react", "node", "fullstack"]

SOURCES = {
    "hn_freelance": fetch_hn_freelance,
    "remoteok": lambda: fetch_remoteok(DEFAULT_TAGS),
    "wwr": fetch_wwr,
}


# Tag-filtering the boards doesn't work: RemoteOK posters spray tags for reach
# (a live "Junior Procurement Specialist" carried 45 tags including python,
# java and data science), so tags say nothing about relevance. Filter on the
# engagement model instead, which is what project scope actually cares about —
# employment is out of scope, Manan has a separate job agent for that.
#
# The title is a deliberate claim about the engagement, so a bare word there is
# enough. A description is long prose where "contract" and "consulting" appear
# incidentally (benefits boilerplate, vendor duties) — live WWR rows like
# "Senior Sourcing Analyst" and "Director, Facility Security Officer" slipped
# through on exactly that — so it needs an explicit engagement phrase.
_TITLE_SIGNAL = re.compile(
    r"\b(freelance|freelancer|contract|contractor|part[- ]time|hourly)\b", re.I
)
_BODY_SIGNAL = re.compile(
    r"\b(freelance|freelancer"
    r"|contract (?:role|position|basis|work|opportunity)"
    r"|(?:\d+[- ])?month contract"
    r"|project[- ]based"
    r"|short[- ]term (?:contract|project|engagement))\b", re.I
)
# Sources that are freelance by definition; their posts rarely say the word.
FREELANCE_BY_DEFAULT = {"hn_freelance"}


def is_freelance(job: dict) -> bool:
    if job.get("source") in FREELANCE_BY_DEFAULT:
        return True
    if _TITLE_SIGNAL.search(job.get("title", "")):
        return True
    return bool(_BODY_SIGNAL.search(job.get("description", "")))


def collect_jobs(sources=None) -> list[dict]:
    sources = SOURCES if sources is None else sources
    out = []
    for name, fetch in sources.items():
        try:
            rows = fetch()
        except Exception:
            log.exception("source %s failed; skipping", name)
            continue
        kept = [r for r in rows if is_freelance(r)]
        if len(kept) < len(rows):
            log.info("%s: kept %d/%d rows after freelance filter", name, len(kept), len(rows))
        out.extend(kept)
    return out
