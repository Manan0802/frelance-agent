"""A Facebook page is not a website.

OSM's `website` tag on small businesses very often points at a Facebook page, a
Linktree or a WhatsApp link. Those businesses have no site at all — they are the
segment with the strongest pitch (the absence is a verified fact). Treating the
tag as "has a website" sends them the researched angle, which is explicitly told
NOT to offer to build a website, so the best lead gets the weakest pitch.

Fetching the URL doesn't catch it either: facebook.com returns a perfectly good
200, so `has_source` comes back True and the model writes about a site it never
really read.
"""

from backend.engine_b.research import is_social_only, research_target


class Target:
    name = "Kensington Joinery"
    category = "carpenter"
    location = "Manchester, UK"
    website = "https://www.facebook.com/kensingtonjoinery"


def test_social_pages_are_not_websites():
    for url in [
        "https://www.facebook.com/somebakery",
        "https://facebook.com/pages/x/123",
        "https://www.instagram.com/somegym/",
        "https://linktr.ee/somesalon",
        "https://wa.me/919876543210",
        "https://business.site/x",
    ]:
        assert is_social_only(url), url


def test_a_real_site_is_not_social():
    for url in [
        "https://daybreakdentalcare.com",
        "https://www.austinurbanvet.com/contact",
        "https://joinery.co.uk",
    ]:
        assert not is_social_only(url), url


def test_a_blank_website_is_not_social_only():
    """No website at all is its own case — already handled upstream."""
    assert not is_social_only("")


def test_research_does_not_fetch_a_social_page():
    """facebook.com returns 200, so fetching it would set has_source True and let
    the model invent detail about a site it never read."""
    calls = []

    out = research_target(
        Target(),
        fetch=lambda url: calls.append(url) or "<html>facebook</html>",
        llm=lambda p: '{"research_summary": "s", "pain_points": "p"}',
    )

    assert calls == [], "must not fetch the social page"
    assert out["has_source"] is False


def test_research_still_reads_a_real_site():
    real = type("T", (), dict(Target.__dict__))
    real.website = "https://joinery.co.uk"
    calls = []

    out = research_target(
        real(),
        fetch=lambda url: calls.append(url) or "<html>real site</html>",
        llm=lambda p: '{"research_summary": "s", "pain_points": "p"}',
    )

    assert calls == ["https://joinery.co.uk"]
    assert out["has_source"] is True
