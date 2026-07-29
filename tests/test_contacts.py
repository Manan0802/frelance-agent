"""A draft with no address is not a lead.

Overpass carries an `email` tag for almost nobody, so the only place a contact
actually exists for the has-website segment is the business's own site — in a
mailto: link, a footer, or behind a contact page. These tests pin the extraction
and, just as importantly, the rejections: a live pass over real sites returns
far more `image@2x.png` and `noreply@wixpress.com` than real addresses.
"""

from backend.engine_b.contacts import find_contact, emails_in


def test_reads_a_mailto_link():
    html = '<a href="mailto:hello@dentist.co.uk">Email us</a>'
    assert emails_in(html) == ["hello@dentist.co.uk"]


def test_reads_a_bare_address_in_the_footer():
    html = "<footer>Call 020 1234 or write to info@acmeplumbing.com</footer>"
    assert emails_in(html) == ["info@acmeplumbing.com"]


def test_rejects_asset_filenames_that_look_like_addresses():
    """`logo@2x.png` matches a naive email regex. Live sites are full of them."""
    html = '<img src="/img/logo@2x.png"><img src="hero@3x.jpg">'
    assert emails_in(html) == []


def test_rejects_platform_and_placeholder_addresses():
    html = """
      noreply@wixpress.com you@example.com name@yourdomain.com
      no-reply@squarespace.com sentry@sentry.io real@bakery.ie
    """
    assert emails_in(html) == ["real@bakery.ie"]


def test_deduplicates_and_keeps_first_seen_order():
    html = "a@shop.com b@shop.com a@shop.com"
    assert emails_in(html) == ["a@shop.com", "b@shop.com"]


def test_finds_the_email_on_the_homepage():
    def fake_fetch(url):
        assert url == "https://cafe.ie"
        return '<a href="mailto:hi@cafe.ie">say hi</a>'

    assert find_contact("https://cafe.ie", fetch=fake_fetch) == {
        "email": "hi@cafe.ie",
        "contact_url": None,
    }


def test_follows_the_contact_page_when_the_homepage_has_no_address():
    pages = {
        "https://gym.de": '<nav><a href="/kontakt">Kontakt</a></nav>',
        "https://gym.de/kontakt": "schreib uns: team@gym.de",
    }

    assert find_contact("https://gym.de", fetch=lambda u: pages.get(u, "")) == {
        "email": "team@gym.de",
        "contact_url": "https://gym.de/kontakt",
    }


def test_returns_the_contact_page_alone_when_it_is_only_a_form():
    """Most modern sites hide the address behind a form. The form URL is still a
    delivery channel — it just costs Manan a manual submit."""
    pages = {
        "https://firm.com": '<a href="/contact-us">Contact us</a>',
        "https://firm.com/contact-us": "<form><input name=message></form>",
    }

    assert find_contact("https://firm.com", fetch=lambda u: pages.get(u, "")) == {
        "email": None,
        "contact_url": "https://firm.com/contact-us",
    }


def test_prefers_an_address_on_the_business_own_domain():
    """Live Austin data: a dental practice published `webreporting@gargle.com`
    (their marketing vendor) above their own address. Pitching the vendor wastes
    the lead, so the business's own domain wins when both are on the page."""
    pages = {"https://daybreakdentalcare.com":
             "webreporting@gargle.com admin@daybreakdentalcare.com"}

    assert find_contact("https://daybreakdentalcare.com",
                        fetch=lambda u: pages[u])["email"] == "admin@daybreakdentalcare.com"


def test_www_and_subdomains_still_count_as_the_business_own_domain():
    pages = {"https://www.austinurbanvet.com": "x@vendor.com info@austinurbanvet.com"}
    assert find_contact("https://www.austinurbanvet.com",
                        fetch=lambda u: pages[u])["email"] == "info@austinurbanvet.com"


def test_an_off_domain_address_is_still_used_when_it_is_all_there_is():
    """Small businesses run on gmail constantly — off-domain is not a reject."""
    pages = {"https://afterhourskids.com": "afterhourskids@gmail.com"}
    assert find_contact("https://afterhourskids.com",
                        fetch=lambda u: pages[u])["email"] == "afterhourskids@gmail.com"


def test_no_website_means_no_contact_and_no_fetch():
    calls = []

    def fake_fetch(url):
        calls.append(url)
        return ""

    assert find_contact("", fetch=fake_fetch) == {"email": None, "contact_url": None}
    assert calls == []


def test_a_social_page_is_not_worth_fetching():
    """A Facebook page carries no business address and blocks scrapers anyway —
    spending a fetch on it is pure cost. Those leads are reached by phone."""
    calls = []

    out = find_contact("https://www.facebook.com/somebakery",
                       fetch=lambda u: calls.append(u) or "info@facebook.com")

    assert calls == []
    assert out == {"email": None, "contact_url": None}


def test_a_dead_site_is_not_an_error():
    """Cron runs this over hundreds of sites; a 500 must not end the run."""
    def boom(url):
        raise RuntimeError("connection reset")

    assert find_contact("https://dead.com", fetch=boom) == {
        "email": None,
        "contact_url": None,
    }
