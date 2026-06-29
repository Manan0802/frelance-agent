from backend.database.connection import engine, SessionLocal
from backend.database.models import OutboundTarget, create_all


def test_insert_target():
    create_all(engine)
    db = SessionLocal()
    t = OutboundTarget(id="t1", name="Acme Dental", dedup_hash="h1", raw="{}")
    db.add(t)
    db.commit()
    got = db.query(OutboundTarget).filter_by(id="t1").one()
    assert got.name == "Acme Dental"
    db.close()
