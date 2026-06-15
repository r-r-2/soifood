"""Route: GET /qr/{id} — PNG QR code for the vendor URL."""

import io

from PIL import Image


def test_qr_returns_png(client):
    r = client.get("/qr/1")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"

    data = r.content
    assert data[:8] == b"\x89PNG\r\n\x1a\n"

    img = Image.open(io.BytesIO(data))
    assert img.format == "PNG"
    assert img.size[0] > 0
    assert img.size[1] > 0


def test_qr_works_for_nonexistent_vendor_id(client):
    """QR encodes a URL — generation doesn't check vendor existence."""
    r = client.get("/qr/99999")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
