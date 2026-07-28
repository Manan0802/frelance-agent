"""The daily run — Engine B, end to end, unattended.

Manan asked for Engine B to work on his behalf: source businesses, research
them, draft the pitch, and have it all waiting without him driving anything.
This is that entrypoint, meant for cron.

**It never contacts a client.** Drafts land in the review queue and the only
outbound message is a summary to Manan. Sending is a separate decision with its
own constraints — deliverability limits and the legal position are in BUILD_LOG
Phase 13, and the project's founding rule is that a human approves before a
client hears anything.

Two things keep an unattended run sane:
- **City rotation**, derived from the date, so consecutive mornings work
  different cities instead of re-pitching the same street. Date-derived means
  cron needs no state file.
- **Bounds.** One city can return ~480 businesses and each costs several LLM
  calls; a run over all 214 cities would be a very expensive morning.
"""

import logging
from datetime import datetime

from backend.engine_b.areas import AREAS
from backend.engine_b.overpass_source import fetch_overpass
from backend.engine_b.ingest import ingest_targets
from backend.engine_b.graph import run_engine_b
from backend.notify.whatsapp import send_whatsapp
from backend.portfolio.context import load_portfolio

log = logging.getLogger(__name__)

EPOCH = datetime(2026, 1, 1)
AREAS_PER_RUN = 3
MAX_TARGETS_PER_RUN = 40


def reachable_first(rows: list[dict]) -> list[dict]:
    """Spend the daily cap where a contact can actually be found.

    Measured on Austin: half the website-having rows yield an email or a contact
    form, against 8% of the no-website rows yielding even a phone. Taking the
    first 40 rows in Overpass order fills the morning queue with businesses
    nobody can reach. The no-website rows still follow — they're the better
    pitch when a channel exists, they just can't lead.
    """
    return sorted(rows, key=lambda r: not (r.get("website") or r.get("email")))


def _today_index() -> int:
    return (datetime.utcnow() - EPOCH).days


def pick_areas_for_run(day_index: int | None = None, per_run: int = AREAS_PER_RUN):
    """A rotating slice of cities. Derived from the date so cron keeps no state,
    and wraps around so it never runs out."""
    labels = list(AREAS)
    index = _today_index() if day_index is None else day_index
    start = (index * per_run) % len(labels)
    picked = [labels[(start + i) % len(labels)] for i in range(per_run)]
    return [(label, AREAS[label]) for label in picked]


def run_daily(
    db,
    fetch=fetch_overpass,
    ingest=ingest_targets,
    run_engine=run_engine_b,
    notify=send_whatsapp,
    day_index: int | None = None,
    per_run: int = AREAS_PER_RUN,
    max_targets: int = MAX_TARGETS_PER_RUN,
    portfolio_path: str = "data/portfolio_context.json",
) -> dict:
    areas = pick_areas_for_run(day_index, per_run)
    result = {"areas": [a for a, _ in areas], "targets": 0,
              "messages_drafted": 0, "sent_to_clients": 0, "error": None}

    # Nobody is watching cron. A dead Overpass mirror must not turn into a
    # silently broken daily job.
    try:
        rows = fetch(areas)
    except Exception as exc:
        log.exception("daily run: sourcing failed")
        result["error"] = f"sourcing failed: {exc}"
        return result

    targets = ingest(reachable_first(rows)[:max_targets], db)
    result["targets"] = len(targets)
    if not targets:
        # Everything may already be in the DB from an earlier run — that's a
        # normal outcome, not a failure.
        log.info("daily run: no new businesses in %s", result["areas"])
        return result

    try:
        messages = run_engine(targets, db, load_portfolio(portfolio_path))
    except Exception as exc:
        log.exception("daily run: drafting failed")
        result["error"] = f"drafting failed: {exc}"
        return result

    result["messages_drafted"] = len(messages)
    notify(
        f"Daily run: {len(messages)} new drafts from {', '.join(result['areas'])}. "
        f"Review and send them from the dashboard — nothing has been sent."
    )
    return result
