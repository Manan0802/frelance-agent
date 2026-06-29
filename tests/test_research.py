from backend.engine_b.research import research_target, _is_safe_url


def test_ssrf_guard_blocks_internal_addresses():
    assert _is_safe_url("http://127.0.0.1/") is False
    assert _is_safe_url("http://169.254.169.254/latest/meta-data/") is False
    assert _is_safe_url("http://10.0.0.5/") is False
    assert _is_safe_url("file:///etc/passwd") is False
    assert _is_safe_url("http://0.0.0.0/") is False
    assert _is_safe_url("https://8.8.8.8/") is True


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
