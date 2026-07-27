"""Reddit r/forhire + r/hiring via RSS.

Correction to an earlier finding on this project: Reddit's `.json` endpoints
403 without OAuth, but the **`.rss` path is open and unauthenticated** (verified
200, ~68KB of real content). No app registration needed.

Same shape of trap as the HN thread: the subs mix `[HIRING]` (a client with
work) and `[FOR HIRE]` (freelancers advertising themselves — competitors).
Measured live, only ~24% are client-side, so the filter is the feature.

Reddit rate-limits hard on this path — observed `x-ratelimit-remaining: 0`
after a single request, resetting in ~13s — so fetching must tolerate 429 and
back off rather than hammering a free endpoint.
"""

from backend.engine_a.reddit import fetch_reddit, _is_hiring, SUBREDDITS


def test_keeps_client_posts():
    assert _is_hiring("[HIRING] Remote Performance Marketer for Meta and Google Ads")
    assert _is_hiring("[Hiring] Recreate Existing PNG Logo as SVG")


def test_drops_freelancers_advertising_themselves():
    """These are competitors, not leads."""
    assert not _is_hiring("[FOR HIRE] Video Editor, Graphic Designer available")
    assert not _is_hiring("[for hire] Fullstack developer- React, Next.js- $20/hour")
    assert not _is_hiring("[For Hire] Bot Building | Web Scraping | Automation")


def test_for_hire_is_not_mistaken_for_hiring():
    """'[FOR HIRE]' contains 'hire'; a sloppy substring check flips the meaning
    of the post and fills the pipeline with competitor ads."""
    assert not _is_hiring("[FOR HIRE] I am hiring myself out as a developer")


def test_only_the_tag_at_the_start_decides():
    assert not _is_hiring("[FOR HIRE] dev available, I know you are hiring")


def test_maps_entries_to_the_common_job_shape():
    def fake_parse(url):
        assert "/r/forhire/new/.rss" in url
        return [
            {"title": "[HIRING] Build a Shopify app", "summary": "<p>Need it in 2 weeks</p>",
             "link": "https://reddit.com/r/forhire/1"},
            {"title": "[FOR HIRE] React dev available", "summary": "hire me",
             "link": "https://reddit.com/r/forhire/2"},
        ]

    rows = fetch_reddit(subreddits=["forhire"], parse=fake_parse, spacing=0)

    assert len(rows) == 1
    r = rows[0]
    assert r["source"] == "reddit"
    assert r["title"] == "[HIRING] Build a Shopify app"
    assert "<p>" not in r["description"], "HTML must be stripped"
    assert r["url"] == "https://reddit.com/r/forhire/1"
    assert r["location"] == "", "Reddit posts carry no structured location"


def test_reads_every_configured_subreddit():
    seen = []

    def fake_parse(url):
        seen.append(url)
        return []

    fetch_reddit(subreddits=["forhire", "hiring"], parse=fake_parse, spacing=0)
    assert len(seen) == 2


def test_one_failing_subreddit_does_not_lose_the_others():
    """Reddit 429s readily; losing one sub must not cost the whole fetch."""
    def fake_parse(url):
        if "forhire" in url:
            raise RuntimeError("429 Too Many Requests")
        return [{"title": "[HIRING] Django work", "summary": "s", "link": "u"}]

    rows = fetch_reddit(subreddits=["forhire", "hiring"], parse=fake_parse, spacing=0)
    assert [r["title"] for r in rows] == ["[HIRING] Django work"]


def test_default_subreddits_are_the_ones_with_measured_client_demand():
    assert "forhire" in SUBREDDITS and "hiring" in SUBREDDITS
