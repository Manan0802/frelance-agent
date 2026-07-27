"""Reddit r/forhire + r/hiring via RSS.

Correcting an earlier finding on this project: the `.json` endpoints 403
without OAuth, but the **`.rss` path is open and unauthenticated** (verified
200). No app registration needed.

Measured live: ~24% of posts are `[HIRING]` (a client with work); the rest are
`[FOR HIRE]` — freelancers advertising themselves, i.e. competitors. Across
r/forhire and r/hiring that's roughly 100 client posts a week, far more than
any other free source here.

Reddit rate-limits this path hard (observed `x-ratelimit-remaining: 0` after a
single request, ~13s reset), so requests are spaced and a failing subreddit is
skipped rather than taking the run down.
"""

import html
import logging
import re
import time

FEED = "https://www.reddit.com/r/{sub}/new/.rss"
SUBREDDITS = ["forhire", "hiring"]
# Reddit allows roughly one request per 13s on this path.
REQUEST_SPACING_SECONDS = 14

# "[FOR HIRE]" contains "hire", so a substring check inverts the meaning of the
# post. Anchor to the tag at the start, and require HIRING not preceded by FOR.
_HIRING_TAG = re.compile(r"^\s*\[\s*hiring\s*\]", re.I)
_TAG = re.compile(r"<[^>]+>")

log = logging.getLogger(__name__)


def _default_parse(url: str):
    import feedparser

    return feedparser.parse(url).entries


def _clean(text: str) -> str:
    return html.unescape(_TAG.sub(" ", text or "")).strip()


def _is_hiring(title: str) -> bool:
    return bool(_HIRING_TAG.match(title or ""))


def fetch_reddit(subreddits=None, parse=_default_parse, spacing=REQUEST_SPACING_SECONDS) -> list[dict]:
    subs = SUBREDDITS if subreddits is None else subreddits
    out = []
    for i, sub in enumerate(subs):
        if i and spacing:
            time.sleep(spacing)
        try:
            entries = parse(FEED.format(sub=sub))
        except Exception:
            log.exception("reddit r/%s failed; skipping", sub)
            continue
        for e in entries:
            title = e.get("title", "")
            if not _is_hiring(title):
                continue
            out.append(
                {
                    "source": "reddit",
                    "title": title,
                    "description": _clean(e.get("summary", "")),
                    "url": e.get("link"),
                    "budget": None,
                    "location": "",
                }
            )
    return out
