"""Route: GET /order-audio?text=... — Thai TTS MP3 stream."""

import main


def test_order_audio_returns_mp3(client):
    r = client.get("/order-audio", params={"text": "ผัดไทย 1 จาน"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/mpeg"
    # The mock writes ID3-prefixed fake bytes.
    assert r.content.startswith(b"ID3")


def test_order_audio_returns_503_when_tts_fails(client, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("gtts down")

    monkeypatch.setattr(main, "gTTS", _boom)

    r = client.get("/order-audio", params={"text": "fail me"})
    assert r.status_code == 503


def test_order_audio_uses_thai_lang(client, monkeypatch):
    captured = {}

    class _Spy:
        def __init__(self, text, lang, slow=False):
            captured["text"] = text
            captured["lang"] = lang

        def write_to_fp(self, fp):
            fp.write(b"ID3-spy")

    monkeypatch.setattr(main, "gTTS", _Spy)

    client.get("/order-audio", params={"text": "ขอบคุณ"})
    assert captured["lang"] == "th"
    assert captured["text"] == "ขอบคุณ"
