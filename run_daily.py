#!/usr/bin/env python
"""Daily Engine B run — point cron at this.

    0 8 * * *  cd /path/to/freea && ./venv/bin/python run_daily.py >> daily.log 2>&1

Sources businesses for a rotating slice of cities, researches each, drafts a
pitch, and leaves everything in the review queue. **Nothing is sent to a
client** — the only message that leaves is a summary to Manan.

Options:
    --areas Austin London     specific cities instead of the daily rotation
    --per-run N               how many cities this run (default 3)
    --max-targets N           cap on businesses processed (default 40)
    --dry-run                 source and report, draft nothing (no LLM cost)
"""

import argparse
import logging
import sys

from backend.automation.daily import run_daily, pick_areas_for_run, AREAS_PER_RUN, MAX_TARGETS_PER_RUN
from backend.database.connection import SessionLocal, engine
from backend.database.models import create_all
from backend.engine_b.areas import areas_for
from backend.engine_b.overpass_source import fetch_overpass


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--areas", nargs="*", help="city or country names, e.g. Austin London India")
    p.add_argument("--per-run", type=int, default=AREAS_PER_RUN)
    p.add_argument("--max-targets", type=int, default=MAX_TARGETS_PER_RUN)
    p.add_argument("--dry-run", action="store_true", help="source only; draft nothing")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    create_all(engine)
    db = SessionLocal()
    try:
        if args.dry_run:
            areas = (areas_for(args.areas) if args.areas
                     else pick_areas_for_run(per_run=args.per_run))
            rows = fetch_overpass(areas)
            no_site = sum(1 for r in rows if not r["website"])
            print(f"{len(rows)} businesses across {[a for a, _ in areas]}")
            print(f"  {no_site} with no website, {sum(1 for r in rows if r['phone'])} with a phone")
            print("  (dry run — nothing drafted, nothing sent)")
            return 0

        fetch = (lambda _areas: fetch_overpass(areas_for(args.areas))) if args.areas else fetch_overpass
        result = run_daily(db, fetch=fetch, per_run=args.per_run, max_targets=args.max_targets)

        print(f"areas:    {', '.join(result['areas'])}")
        print(f"targets:  {result['targets']} new")
        print(f"drafted:  {result['messages_drafted']}")
        print(f"sent to clients: {result['sent_to_clients']}  (always 0 — review in /dashboard)")
        if result["error"]:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            return 1
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
