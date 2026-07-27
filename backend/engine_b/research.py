import ipaddress
import socket
from urllib.parse import urlparse

import httpx

from backend.llm.gemini import generate
from backend.llm.parse import parse_json


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
{grounding}{capabilities}
Return ONLY JSON: {{"research_summary": "...", "pain_points": "concrete problems this developer could fix for them"}}"""

CAPABILITY_NOTE = """
THE DEVELOPER PITCHING THEM BUILDS: {capabilities}.

Look for openings in THOSE areas only — work that is repetitive or manual for this business,
things a customer can't currently self-serve, questions their staff must answer by hand, and
anything on their site that is missing rather than merely slow. Do NOT return generic web-perf
observations (page speed, image sizes, minification) unless the developer's listed capabilities
actually cover them: those read as nitpicking and this developer cannot pitch them credibly.
"""

UNGROUNDED_NOTE = """
NOTE: no website content was retrieved. You know nothing about this business beyond its name,
category and location. Do NOT state specifics about their products, customers, history or
operations — say only what follows from the category itself, and keep the summary short.
"""


def capability_summary(portfolio) -> str:
    """What this developer can actually deliver, drawn from the portfolio's own
    pitch_for tags — so research hunts for openings he can credibly pitch."""
    seen, out = set(), []
    for p in portfolio.projects:
        for tag in p.pitch_for:
            key = tag.lower()
            if key not in seen:
                seen.add(key)
                out.append(tag)
    return ", ".join(out)


def research_target(target, portfolio=None, fetch=_default_fetch, llm=generate) -> dict:
    site = fetch(target.website) if target.website else ""
    has_source = bool(site)
    caps = capability_summary(portfolio) if portfolio else ""
    prompt = RESEARCH_PROMPT.format(
        name=target.name,
        category=target.category or "business",
        location=target.location or "",
        site=site or "(no website found)",
        grounding="" if has_source else UNGROUNDED_NOTE,
        capabilities=CAPABILITY_NOTE.format(capabilities=caps) if caps else "",
    )
    raw = llm(prompt)
    out = parse_json(raw, {"research_summary": raw.strip(), "pain_points": ""})
    out["has_source"] = has_source
    return out
