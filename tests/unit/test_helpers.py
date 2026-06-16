"""Unit tests for the low-level primitives the app relies on:
SHA256 hashing (privacy rule) and QR PNG generation (brand color).
"""
import hashlib
import io

import qrcode


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def test_sha256_hex_is_64_chars_and_lowercase():
    digest = _sha256_hex("0812345678")
    assert len(digest) == 64
    assert digest == digest.lower()
    assert all(c in "0123456789abcdef" for c in digest)


def test_sha256_is_deterministic():
    assert _sha256_hex("0899999999") == _sha256_hex("0899999999")
    assert _sha256_hex("a") != _sha256_hex("b")


def _make_qr_png(url: str) -> bytes:
    """Mirror of the /qr route's image generation."""
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a2f4a", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_qr_generates_valid_png():
    data = _make_qr_png("http://localhost:8000/vendor/1")
    # PNG magic number
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 100


def test_qr_uses_brand_navy():
    """The QR fill color must be the soifood navy #1a2f4a."""
    from PIL import Image

    data = _make_qr_png("http://localhost:8000/vendor/1")
    img = Image.open(io.BytesIO(data)).convert("RGB")
    colors = {c for _, c in img.getcolors(maxcolors=100000)}
    assert (26, 47, 74) in colors  # #1a2f4a
