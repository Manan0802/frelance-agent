"""Find a way to actually reach a business.

Measured on live Overpass data (Austin, 608 businesses): only 60 rows carry an
`email` tag at all, so sourcing gives reach and almost nothing to reach *with*.
For the has-website segment the address is on their own site — a mailto: link, a
footer line, or a form on a contact page. Probing 50 of them found an email for
34% and a contact form for another 16%, taking one city from ~10% contactable to
half the website segment. This module is the delivery half of a lead.

Redirects are followed **manually**, re-running the SSRF guard on every hop:
following blindly would let a redirect walk us onto a private address, and not
following at all loses the plain http:// → https:// hop that most business
sites still start with.
"""

import re
from urllib.parse import urljoin, urlparse

import httpx

from backend.engine_b.research import _is_safe_url, is_social_only

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

# Everything here appeared in live pages while an address did not.
ASSET_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico")
JUNK_DOMAINS = (
    "example.com", "example.org", "yourdomain", "domain.com", "email.com",
    "sentry.io", "wixpress.com", "squarespace.com", "godaddy.com",
    "@2x", "@3x",
)
JUNK_LOCALS = ("noreply", "no-reply", "donotreply")

CONTACT_HINTS = ("contact", "kontakt", "contacto", "contatti", "kontakta", "reach-us")

MAX_REDIRECTS = 3
# Measured, not guessed: dishoom.com is 1.05MB and deliciouslyella.com 1.15MB of
# mostly inline JS, and the contact link and footer address sit past the first
# 200KB. A 200KB cap found nothing on either. Read the page or don't bother.
MAX_PAGE_BYTES = 2_000_000


def emails_in(html: str) -> list[str]:
    """Real addresses only, first-seen order kept — the first address on a page
    is nearly always the general one rather than a staff member's."""
    out = []
    for raw in EMAIL_RE.findall(html or ""):
        addr = raw.lower().rstrip(".")
        if addr.endswith(ASSET_SUFFIXES):
            continue
        if any(j in addr for j in JUNK_DOMAINS):
            continue
        if addr.split("@")[0] in JUNK_LOCALS:
            continue
        if addr not in out:
            out.append(addr)
    return out


def _default_fetch(url: str, _depth: int = 0) -> str:
    if _depth > MAX_REDIRECTS or not _is_safe_url(url):
        return ""
    try:
        r = httpx.get(
            url,
            timeout=15,
            follow_redirects=False,
            headers={"User-Agent": "FreelancingAgent/1.0"},
        )
    except Exception:
        return ""
    location = r.headers.get("location")
    if r.is_redirect and location:
        return _default_fetch(urljoin(url, location), _depth + 1)
    return r.text[:MAX_PAGE_BYTES]


def _site_domain(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def best_email(found: list[str], website: str) -> str | None:
    """The business's own domain wins. Live Austin data: a dental practice
    published `webreporting@gargle.com` — their marketing vendor — above their
    own address, and a DSO group inbox above the individual clinic. Pitching the
    vendor wastes the lead. Off-domain is not a reject though: small businesses
    run on gmail constantly."""
    if not found:
        return None
    domain = _site_domain(website)
    if domain:
        for addr in found:
            if addr.endswith("@" + domain) or addr.endswith("." + domain):
                return addr
    return found[0]


def _contact_page(html: str, base: str) -> str | None:
    for href in re.findall(r'href=["\']([^"\']+)["\']', html or ""):
        if any(h in href.lower() for h in CONTACT_HINTS) and not href.startswith("mailto:"):
            url = urljoin(base, href)
            if urlparse(url).netloc == urlparse(base).netloc:
                return url
    return None


def find_contact(website: str, fetch=_default_fetch) -> dict:
    """`{"email", "contact_url"}` — either is a channel Manan can use; both None
    means this lead is drafted but undeliverable."""
    none = {"email": None, "contact_url": None}
    if not website or is_social_only(website):
        return none

    try:
        home = fetch(website)
    except Exception:
        return none
    if not home:
        return none

    found = emails_in(home)
    if found:
        return {"email": best_email(found, website), "contact_url": None}

    page = _contact_page(home, website)
    if not page:
        return none
    try:
        html = fetch(page)
    except Exception:
        return {"email": None, "contact_url": page}

    return {"email": best_email(emails_in(html), website), "contact_url": page}
