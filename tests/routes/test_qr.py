"""Tests for GET /qr/{id} (QR PNG)."""


def test_qr_returns_png(client):
    r = client.get("/qr/1")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_qr_works_for_nonexistent_vendor_id(client):
    # The QR route encodes a URL; it does not look up the vendor.
    r = client.get("/qr/99999")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
