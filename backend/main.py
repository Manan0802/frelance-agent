from fastapi import FastAPI

from backend.api.routes import router, set_run_deps  # noqa: F401

app = FastAPI(title="Freelancing Agent")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(router)
