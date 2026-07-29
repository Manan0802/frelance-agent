"""A block page is not their website.

Found in real drafts from the first live Austin run:

    "Your website's 403 error is hiding your patient support info"
    "You're currently using a Cloudflare challenge page"

Neither business had a broken site. Those were *our* fetcher being blocked, and
because neither fetcher checked the status code, the error page came back as
site content — so `has_source` was True and the model confidently described a
problem that did not exist. Telling a business their website is broken when it
isn't ends the conversation on the first line.
"""

from unittest.mock import MagicMock, patch

from backend.engine_b import contacts, research


def _safe(monkeypatch):
    """The SSRF guard does a real DNS lookup; without stubbing it these tests
    would pass for the wrong reason (no network -> empty string either way)."""
    monkeypatch.setattr(research, "_is_safe_url", lambda url: True)


def _response(status: int, text: str):
    r = MagicMock()
    r.status_code = status
    r.text = text
    r.is_redirect = False
    r.headers = {}
    return r


def test_research_treats_a_403_as_no_content(monkeypatch):
    _safe(monkeypatch)
    with patch("backend.engine_b.research.httpx.get",
               return_value=_response(403, "<html>Access denied</html>")):
        assert research._default_fetch("https://blocked.com") == ""


def test_research_treats_a_500_as_no_content(monkeypatch):
    _safe(monkeypatch)
    with patch("backend.engine_b.research.httpx.get",
               return_value=_response(500, "<html>Server Error</html>")):
        assert research._default_fetch("https://broken.com") == ""


def test_research_still_reads_a_200(monkeypatch):
    _safe(monkeypatch)
    with patch("backend.engine_b.research.httpx.get",
               return_value=_response(200, "<html>real content</html>")):
        assert "real content" in research._default_fetch("https://fine.com")


def test_contacts_treats_a_403_as_no_content(monkeypatch):
    """Same fault, second fetcher — a Cloudflare challenge page carries no
    address, and any string it does contain is not the business's."""
    _safe(monkeypatch)
    with patch("backend.engine_b.contacts.httpx.get",
               return_value=_response(403, "support@cloudflare.com")):
        assert contacts._default_fetch("https://blocked.com") == ""


def test_contacts_still_reads_a_200(monkeypatch):
    _safe(monkeypatch)
    with patch("backend.engine_b.contacts.httpx.get",
               return_value=_response(200, "hi@shop.com")):
        assert contacts._default_fetch("https://shop.com") == "hi@shop.com"
