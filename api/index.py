"""Vercel entrypoint — the review dashboard only.

Deliberately not the whole app. The engine needs sentence-transformers (torch,
far past Vercel's function size limit), Overpass calls that can run for the
better part of an hour, and LLM keys. None of that belongs in a serverless
function, and none of it is what Manan wants from a hosted page: he wants to
*look* at the queue from his phone.

So the split is engine on his Mac, viewer on Vercel, one shared Postgres. That
also means DATABASE_URL here must point at Postgres — Vercel's filesystem is
read-only and per-invocation, so a SQLite file would be empty on every request.

The torch import in matcher.py is lazy and this app never triggers it, so the
dependency stays out of the deployment entirely (see api/requirements.txt).
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.api.dashboard import router as dashboard_router, require_password_for_deploy
from backend.config import settings
from backend.database.connection import engine
from backend.database.models import create_all

# Refuses to boot rather than publishing the pipeline unprotected.
require_password_for_deploy(settings.dashboard_password)

if settings.database_url.startswith("sqlite"):
    raise RuntimeError(
        "DATABASE_URL points at SQLite. Vercel's filesystem is read-only and "
        "per-invocation, so the dashboard would render an empty queue on every "
        "request. Point it at the Postgres the engine writes to."
    )

app = FastAPI(title="Freelancing Agent — review dashboard")
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "backend" / "static")),
    name="static",
)
app.include_router(dashboard_router)

create_all(engine)


@app.get("/")
def root():
    return {"dashboard": "/dashboard"}
