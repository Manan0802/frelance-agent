from unittest.mock import MagicMock, patch

from backend.llm import gemini


def test_generate_uses_default_model_and_returns_text():
    fake_response = MagicMock(text="hello world")
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("backend.llm.gemini.genai.Client", return_value=fake_client) as mock_client_cls:
        result = gemini.generate("some prompt")

    mock_client_cls.assert_called_once_with(api_key=gemini.settings.gemini_api_key)
    fake_client.models.generate_content.assert_called_once_with(
        model=gemini.DEFAULT_MODEL, contents="some prompt"
    )
    assert result == "hello world"


def test_generate_accepts_model_override():
    fake_response = MagicMock(text="ok")
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with patch("backend.llm.gemini.genai.Client", return_value=fake_client):
        gemini.generate("prompt", model="gemini-2.5-flash")

    fake_client.models.generate_content.assert_called_once_with(
        model="gemini-2.5-flash", contents="prompt"
    )


def test_generate_falls_back_to_groq_on_gemini_failure(monkeypatch):
    monkeypatch.setattr(gemini.settings, "groq_api_key", "fake-groq-key")

    fake_groq_response = MagicMock()
    fake_groq_response.raise_for_status.return_value = None
    fake_groq_response.json.return_value = {
        "choices": [{"message": {"content": "groq says hi"}}]
    }

    with patch("backend.llm.gemini.genai.Client", side_effect=RuntimeError("quota exceeded")):
        with patch("backend.llm.gemini.httpx.post", return_value=fake_groq_response) as mock_post:
            result = gemini.generate("prompt")

    assert result == "groq says hi"
    called_url, called_kwargs = mock_post.call_args[0][0], mock_post.call_args[1]
    assert "groq.com" in called_url
    assert called_kwargs["headers"]["Authorization"] == "Bearer fake-groq-key"
    assert called_kwargs["json"]["messages"][0]["content"] == "prompt"


def test_both_providers_rate_limited_is_retried_not_fatal():
    """Measured on a real 25-target run: 125 calls in a burst 429'd Gemini, fell
    through to Groq, and 429'd that too — killing the whole run. Both free tiers
    are per-minute limited, so waiting is the only cure."""
    calls = {"gemini": 0}
    slept = []

    def flaky_client(**kw):
        calls["gemini"] += 1
        if calls["gemini"] < 3:
            raise RuntimeError("429 Too Many Requests")
        fake = MagicMock()
        fake.models.generate_content.return_value = MagicMock(text="finally")
        return fake

    with patch("backend.llm.gemini.genai.Client", side_effect=flaky_client):
        with patch("backend.llm.gemini._generate_groq", side_effect=RuntimeError("429")):
            out = gemini.generate("prompt", sleep=slept.append)

    assert out == "finally"
    assert slept, "must back off between attempts, not hammer the endpoint"


def test_gives_up_with_the_real_error_after_the_last_attempt():
    """The caller needs the provider's error, not a generic one, to tell a rate
    limit apart from a bad key."""
    import pytest

    with patch("backend.llm.gemini.genai.Client", side_effect=RuntimeError("bad key")):
        with patch("backend.llm.gemini._generate_groq", side_effect=RuntimeError("groq down")):
            with pytest.raises(RuntimeError, match="groq down"):
                gemini.generate("prompt", sleep=lambda s: None)
