from backend.engine_a.weworkremotely import fetch_wwr


def test_fetch_wwr_maps_entries():
    fake_parse = lambda url: [
        {"title": "Senior React Dev", "summary": "build UI", "link": "http://wwr/1"},
    ]
    out = fetch_wwr(feeds=["http://one"], parse=fake_parse)
    assert len(out) == 1
    assert out[0]["source"] == "wwr"
    assert out[0]["title"] == "Senior React Dev"
    assert out[0]["url"] == "http://wwr/1"
