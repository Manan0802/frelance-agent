from backend.notify.whatsapp import format_digest, send_whatsapp


def test_format_digest():
    text = format_digest([{"name": "Acme Dental", "score": 9.0, "draft_text": "Hi..."}])
    assert "Acme Dental" in text and "9" in text


def test_send_posts_to_greenapi(monkeypatch):
    # explicit, so the result doesn't depend on the developer's local .env
    from backend.config import settings

    monkeypatch.setattr(settings, "whatsapp_enabled", True)
    captured = {}

    class Resp:
        status_code = 200

    def fake_poster(url, json):
        captured["url"] = url
        captured["json"] = json
        return Resp()

    ok = send_whatsapp("hello", poster=fake_poster)
    assert ok is True
    assert "sendMessage" in captured["url"]
    assert captured["json"]["message"] == "hello"


def test_whatsapp_can_be_switched_off(monkeypatch):
    """Every live pipeline run fires a real WhatsApp digest at Manan's phone,
    including test runs. A kill switch lets the pipeline be exercised without
    messaging him."""
    from backend.config import settings

    monkeypatch.setattr(settings, "whatsapp_enabled", False)
    called = {"n": 0}

    def fake_poster(url, json):
        called["n"] += 1
        raise AssertionError("must not post when disabled")

    assert send_whatsapp("hello", poster=fake_poster) is False
    assert called["n"] == 0
