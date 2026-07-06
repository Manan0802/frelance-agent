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
