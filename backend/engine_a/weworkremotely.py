FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
]


def _default_parse(url: str):
    import feedparser

    return feedparser.parse(url).entries


def fetch_wwr(feeds: list[str] = FEEDS, parse=_default_parse) -> list[dict]:
    out = []
    for url in feeds:
        for e in parse(url):
            out.append(
                {
                    "source": "wwr",
                    "title": e.get("title", ""),
                    "description": e.get("summary", ""),
                    "url": e.get("link", ""),
                    "budget": None,
                }
            )
    return out
