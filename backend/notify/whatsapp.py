import httpx

from backend.config import settings


def format_digest(messages: list[dict]) -> str:
    lines = ["🚀 OUTBOUND DIGEST", ""]
    for i, m in enumerate(messages, 1):
        lines.append(f"{i}. [{m['score']:.0f}/10] {m['name']}")
        lines.append(m["draft_text"])
        lines.append("")
    lines.append("→ Review + approve in dashboard, then send manually.")
    return "\n".join(lines)


def _default_poster(url, json):
    return httpx.post(url, json=json, timeout=20)


def send_whatsapp(text: str, poster=_default_poster) -> bool:
    if not settings.whatsapp_enabled:
        return False
    url = (
        f"https://api.green-api.com/waInstance{settings.greenapi_id}"
        f"/sendMessage/{settings.greenapi_token}"
    )
    payload = {"chatId": f"{settings.manan_whatsapp}@c.us", "message": text}
    try:
        resp = poster(url, payload)
        return 200 <= resp.status_code < 300
    except Exception:
        return False
