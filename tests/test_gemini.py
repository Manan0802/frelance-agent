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
