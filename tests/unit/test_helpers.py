"""Misc helper tests — QR output, SHA256 utility contracts."""

import hashlib
import io

import qrcode
from PIL import Image


def test_sha256_hex_is_64_chars_and_lowercase():
    h = hashlib.sha256(b"0812345678").hexdigest()
    assert len(h) == 64
    assert h == h.lower()


def test_sha256_is_deterministic():
    assert (
        hashlib.sha256(b"same").hexdigest()
        == hashlib.sha256(b"same").hexdigest()
    )


def test_qr_generates_valid_png():
    """Replicates main.vendor_qr's pipeline shape."""
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data("http://testserver/vendor/1")
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a2f4a", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    data = buf.read()

    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    # Round-trip — PIL can re-read it as an image.
    buf.seek(0)
    reopened = Image.open(buf)
    assert reopened.format == "PNG"
    assert reopened.size[0] > 0


def test_qr_uses_brand_navy():
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data("http://x")
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a2f4a", back_color="white").convert("RGB")

    # Sample the centre pixel — for a small URL, it lands on a dark module
    # or white quiet zone. Either way, fill colour must appear somewhere.
    pixels = set(img.getdata())
    # #1a2f4a as RGB tuple
    assert (26, 47, 74) in pixels
