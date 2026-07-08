from backend.engine_b.maps_source import fetch_google_maps


def test_fetch_google_maps_maps_rows_to_common_shape():
    def fake_scrape(keyword):
        assert keyword == "bakery in Delhi"
        return [
            {
                "title": "Saffron & Sage",
                "address": "Hauz Khas, Delhi",
                "website": "https://saffronsage.example",
                "phone": "+91-9999999999",
                "category": "Bakery",
            }
        ]

    rows = fetch_google_maps(["bakery in Delhi"], scrape=fake_scrape)

    assert rows == [
        {
            "name": "Saffron & Sage",
            "address": "Hauz Khas, Delhi",
            "website": "https://saffronsage.example",
            "phone": "+91-9999999999",
            "email": None,
            "category": "Bakery",
        }
    ]


def test_fetch_google_maps_handles_missing_fields():
    def fake_scrape(keyword):
        return [{"title": "No Website Cafe"}]

    rows = fetch_google_maps(["cafe"], scrape=fake_scrape)

    assert rows[0]["name"] == "No Website Cafe"
    assert rows[0]["website"] is None
    assert rows[0]["category"] is None


def test_fetch_google_maps_queries_all_keywords():
    seen = []

    def fake_scrape(keyword):
        seen.append(keyword)
        return []

    fetch_google_maps(["bakery in Delhi", "gym in Mumbai"], scrape=fake_scrape)

    assert seen == ["bakery in Delhi", "gym in Mumbai"]
