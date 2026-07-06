from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router, set_run_deps, set_inbound_deps  # noqa: F401
from backend.api.dashboard import router as dashboard_router

app = FastAPI(title="Freelancing Agent")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(router)
app.include_router(dashboard_router)
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).resolve().parent / "static")),
    name="static",
)
