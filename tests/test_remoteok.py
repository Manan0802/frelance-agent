from backend.engine_a.remoteok import fetch_remoteok


def test_fetch_remoteok_filters_by_tag():
    fake_http = lambda url: [
        {"legal": "metadata row"},
        {"position": "LangGraph Engineer", "description": "build agents", "url": "http://a", "tags": ["python", "langchain"]},
        {"position": "Plumber", "description": "pipes", "url": "http://b", "tags": ["plumbing"]},
    ]
    out = fetch_remoteok(["langchain"], http=fake_http)
    assert len(out) == 1
    assert out[0]["source"] == "remoteok"
    assert out[0]["title"] == "LangGraph Engineer"
