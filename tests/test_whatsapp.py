from backend.notify.whatsapp import format_digest, send_whatsapp


def test_format_digest():
    text = format_digest([{"name": "Acme Dental", "score": 9.0, "draft_text": "Hi..."}])
    assert "Acme Dental" in text and "9" in text


def test_send_posts_to_greenapi():
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
