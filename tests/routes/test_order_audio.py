"""Tests for GET /order-audio (Thai TTS via gTTS)."""
from unittest.mock import MagicMock, patch


def _fake_gtts_writing_mp3():
    """A gTTS stand-in whose write_to_fp drops MP3-ish bytes into the buffer."""
    def factory(*args, **kwargs):
        inst = MagicMock()

        def write_to_fp(buf):
            buf.write(b"ID3fake-mp3-bytes")
        inst.write_to_fp.side_effect = write_to_fp
        factory.last_kwargs = kwargs
        return inst
    return factory


def test_order_audio_returns_mp3(client):
    with patch("main.gTTS", _fake_gtts_writing_mp3()):
        r = client.get("/order-audio", params={"text": "ผัดไทย 1 จาน"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/mpeg"
    assert r.content.startswith(b"ID3")


def test_order_audio_uses_thai_lang(client):
    fake = _fake_gtts_writing_mp3()
    with patch("main.gTTS", fake):
        client.get("/order-audio", params={"text": "ผัดไทย"})
    assert fake.last_kwargs.get("lang") == "th"


def test_order_audio_returns_503_when_tts_fails(client):
    def boom(*args, **kwargs):
        raise RuntimeError("tts backend down")
    with patch("main.gTTS", boom):
        r = client.get("/order-audio", params={"text": "ผัดไทย"})
    assert r.status_code == 503
