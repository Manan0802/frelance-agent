import ipaddress
import json
import socket
from urllib.parse import urlparse

import httpx

from backend.llm.gemini import generate


def _is_safe_url(url: str) -> bool:
    """Guard against SSRF: allow only http(s) to public hosts."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except (socket.gaierror, UnicodeError):
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return False
    return True


def _default_fetch(url: str) -> str:
    if not _is_safe_url(url):
        return ""
    try:
        r = httpx.get(
            url,
            timeout=15,
            follow_redirects=False,  # don't let redirects bypass the SSRF guard
            headers={"User-Agent": "FreelancingAgent/1.0"},
        )
        return r.text[:6000]
    except Exception:
        return ""


RESEARCH_PROMPT = """You are researching a local business for a freelance pitch.
Business: {name} ({category}) in {location}.
Website content (truncated):
{site}

Return ONLY JSON: {{"research_summary": "...", "pain_points": "concrete problems a web/AI dev could fix"}}"""


def research_target(target, fetch=_default_fetch, llm=generate) -> dict:
    site = fetch(target.website) if target.website else ""
    prompt = RESEARCH_PROMPT.format(
        name=target.name,
        category=target.category or "business",
        location=target.location or "",
        site=site or "(no website found)",
    )
    raw = llm(prompt)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"research_summary": raw.strip(), "pain_points": ""}
