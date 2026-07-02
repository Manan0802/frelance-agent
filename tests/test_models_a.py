from backend.database.connection import engine, SessionLocal
from backend.database.models import create_all, JobLead


def test_insert_job_lead():
    create_all(engine)
    db = SessionLocal()
    j = JobLead(id="j1", source="remoteok", title="LangGraph dev", dedup_hash="jh1", raw="{}")
    db.add(j)
    db.commit()
    got = db.query(JobLead).filter_by(id="j1").one()
    assert got.source == "remoteok"
    db.close()
