import hashlib
import json
import uuid

from backend.database.models import OutboundTarget


def _hash(name: str, location: str) -> str:
    return hashlib.sha256(f"{name}|{location}".encode()).hexdigest()


def ingest_targets(rows: list[dict], db) -> list[OutboundTarget]:
    created = []
    seen: set[str] = set()
    for row in rows:
        name = row.get("name", "").strip()
        location = row.get("address") or row.get("location") or ""
        h = _hash(name, location)
        if h in seen or db.query(OutboundTarget).filter_by(dedup_hash=h).first():
            continue
        seen.add(h)
        t = OutboundTarget(
            id=str(uuid.uuid4()),
            name=name,
            website=row.get("website"),
            email=row.get("email"),
            phone=row.get("phone"),
            category=row.get("category"),
            location=location,
            dedup_hash=h,
            raw=json.dumps(row),
        )
        db.add(t)
        created.append(t)
    db.commit()
    return created
