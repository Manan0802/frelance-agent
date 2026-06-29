from backend.database.connection import engine, SessionLocal
from backend.database.models import create_all, OutboundTarget
from backend.engine_b.ingest import ingest_targets


def test_ingest_dedupes():
    create_all(engine)
    db = SessionLocal()
    rows = [
        {"name": "Acme Dental", "website": "http://acme.in", "address": "Delhi"},
        {"name": "Acme Dental", "website": "http://acme.in", "address": "Delhi"},
    ]
    out = ingest_targets(rows, db)
    assert len(out) == 1
    assert db.query(OutboundTarget).filter_by(name="Acme Dental").count() == 1
    db.close()
