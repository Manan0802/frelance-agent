import httpx


def _default_http(url: str) -> list:
    r = httpx.get(url, timeout=15, headers={"User-Agent": "FreelancingAgent/1.0"})
    return r.json()


def fetch_remoteok(tags: list[str], http=_default_http) -> list[dict]:
    rows = http("https://remoteok.com/api")
    tagset = {t.lower() for t in tags}
    out = []
    for row in rows[1:]:  # index 0 is metadata
        row_tags = {str(t).lower() for t in row.get("tags", [])}
        if tagset and not (tagset & row_tags):
            continue
        out.append(
            {
                "source": "remoteok",
                "title": row.get("position", ""),
                "description": row.get("description", ""),
                "url": row.get("url", ""),
                "budget": row.get("salary") or None,
            }
        )
    return out
