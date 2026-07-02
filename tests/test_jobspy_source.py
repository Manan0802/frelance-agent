from backend.engine_a.jobspy_source import fetch_jobspy


def test_fetch_jobspy_maps_rows():
    fake_scrape = lambda **kw: [
        {"title": "AI Engineer", "description": "RAG pipelines", "job_url": "http://j/1", "min_amount": 2000},
    ]
    out = fetch_jobspy("AI Engineer", scrape=fake_scrape)
    assert len(out) == 1
    assert out[0]["source"] == "jobspy"
    assert out[0]["title"] == "AI Engineer"
    assert out[0]["url"] == "http://j/1"
