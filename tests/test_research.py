from backend.engine_b.research import research_target


class T:
    name = "Acme Dental"
    website = "http://acme.in"
    category = "dentist"
    location = "Delhi"


def test_research_uses_site_and_llm():
    fake_fetch = lambda url: "Acme Dental. Old site, no online booking."
    fake_llm = lambda prompt: (
        '{"research_summary": "Dental clinic, outdated site", '
        '"pain_points": "no online booking"}'
    )
    out = research_target(T(), fetch=fake_fetch, llm=fake_llm)
    assert "Dental" in out["research_summary"]
    assert "booking" in out["pain_points"]
