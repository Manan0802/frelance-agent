import time

import httpx

from backend.config import settings

POLL_INTERVAL = 3.0
POLL_TIMEOUT = 120.0


def _default_scrape(keyword: str) -> list[dict]:
    """Talks to a locally-running gosom/google-maps-scraper REST server
    (docker run gosom/google-maps-scraper -data-folder /gmapsdata) — this
    module does not bundle or start that service. See TOOL_REGISTRY.md."""
    headers = {"X-API-Key": settings.maps_scraper_api_key, "Content-Type": "application/json"}
    base_url = settings.maps_scraper_base_url

    submit = httpx.post(
        f"{base_url}/api/v1/scrape",
        json={"keyword": keyword, "lang": "en", "max_depth": 1},
        headers=headers,
        timeout=15,
    )
    submit.raise_for_status()
    job_id = submit.json()["job_id"]

    elapsed = 0.0
    while elapsed < POLL_TIMEOUT:
        status = httpx.get(f"{base_url}/api/v1/jobs/{job_id}", headers=headers, timeout=15).json()
        if status.get("status") == "completed":
            return status.get("results", [])
        if status.get("status") == "failed":
            return []
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
    return []


def fetch_google_maps(queries: list[str], scrape=_default_scrape) -> list[dict]:
    out = []
    for q in queries:
        for row in scrape(q):
            out.append(
                {
                    "name": row.get("title", ""),
                    "address": row.get("address", ""),
                    "website": row.get("website") or None,
                    "phone": row.get("phone") or None,
                    "email": row.get("email") or None,
                    "category": row.get("category") or None,
                }
            )
    return out
