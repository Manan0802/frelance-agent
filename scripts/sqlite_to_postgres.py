"""Copy the local SQLite queue into the Postgres the hosted dashboard reads.

One-way and idempotent-ish: rows whose primary key already exists are skipped,
so re-running after a new local run only carries the new drafts across.

    ./venv/bin/python scripts/sqlite_to_postgres.py "postgresql+psycopg://..."

The engine keeps running locally against SQLite. This is the sync step until
the engine itself is pointed at Postgres (set DATABASE_URL and it will be).
"""

import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import (
    Base, OutboundTarget, OutreachMessage, JobLead, InboundProposal, CrmRecord,
)

TABLES = [OutboundTarget, JobLead, OutreachMessage, InboundProposal, CrmRecord]


def copy(source_url: str, target_url: str) -> dict:
    src = sessionmaker(bind=create_engine(source_url))()
    dst_engine = create_engine(target_url)
    Base.metadata.create_all(dst_engine)
    dst = sessionmaker(bind=dst_engine)()

    moved = {}
    # Parents before children — OutreachMessage has a FK onto OutboundTarget.
    for model in TABLES:
        existing = {row.id for row in dst.query(model.id).all()}
        rows = [r for r in src.query(model).all() if r.id not in existing]
        for row in rows:
            values = {c.name: getattr(row, c.name) for c in model.__table__.columns}
            dst.add(model(**values))
        dst.commit()
        moved[model.__tablename__] = len(rows)
    src.close()
    dst.close()
    return moved


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: sqlite_to_postgres.py <postgres-url> [sqlite-url]")
    target = sys.argv[1]
    source = sys.argv[2] if len(sys.argv) > 2 else "sqlite:///./data/freelancing_agent.db"
    for table, n in copy(source, target).items():
        print(f"{table:24s} {n} rows copied")
