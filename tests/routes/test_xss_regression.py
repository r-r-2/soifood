"""Regression tests for the stored-XSS finding in /vendors browse page.

Threat model: anyone can POST /onboard with arbitrary q1–q6, including HTML/JS
payloads. The /vendors page renders these fields via innerHTML interpolation.
The fix has two layers:

1. Server-side defensive strip of < > " ` in /onboard before storage.
2. Client-side esc() before every innerHTML interpolation (covered by E2E).

This file asserts layer 1.
"""

import hashlib
import json

from sqlmodel import Session, select

from models import Vendor


def test_onboard_strips_angle_brackets_from_q1(client, engine):
    payload = {
        "q1": "<img src=x onerror=alert(1)>",
        "q2": "ผัดไทย 60 บาท",
        "q3": "Silom <script>evil</script>",
        "q4": "daily 5-11pm",
        "q5": "cash",
        "q6": "story",
        "phone_hash": hashlib.sha256(b"0811111111").hexdigest(),
    }
    r = client.post("/onboard", data=payload, follow_redirects=False)
    assert r.status_code == 303
    new_id = int(r.headers["location"].rsplit("/", 1)[-1])

    with Session(engine) as s:
        v = s.get(Vendor, new_id)
        for field in (
            v.vendor_name_thai, v.thai_food_price, v.thai_location,
            v.thai_hours, v.thai_payment, v.thai_story,
            v.location_thai, v.owner_name,
        ):
            assert "<" not in field, f"angle bracket survived in {field!r}"
            assert ">" not in field, f"angle bracket survived in {field!r}"
            assert '"' not in field
            assert "`" not in field


def test_onboard_preserves_apostrophes_in_names(client, engine):
    """Apostrophe is preserved — needed for names like Auntie Noi's Pad Thai."""
    payload = {
        "q1": "Auntie Noi's stall",
        "q2": "menu",
        "q3": "Silom",
        "q4": "daily",
        "q5": "cash",
        "q6": "story",
        "phone_hash": hashlib.sha256(b"0822222222").hexdigest(),
    }
    r = client.post("/onboard", data=payload, follow_redirects=False)
    new_id = int(r.headers["location"].rsplit("/", 1)[-1])

    with Session(engine) as s:
        v = s.get(Vendor, new_id)
        assert v.vendor_name_thai == "Auntie Noi's stall"


def test_api_vendors_does_not_leak_html(client, engine):
    """Whatever survives sanitization, /api/vendors must not contain raw <>."""
    payload = {
        "q1": "<svg onload=alert(1)>",
        "q2": "<b>bold</b>",
        "q3": "<a href=javascript:alert(1)>",
        "q4": "daily",
        "q5": "cash",
        "q6": "story",
        "phone_hash": hashlib.sha256(b"0833333333").hexdigest(),
    }
    client.post("/onboard", data=payload)

    r = client.get("/api/vendors")
    body = r.text  # raw JSON text
    # No literal < or > characters anywhere in the response.
    # (JSON-encoded would still be "<" — they are NOT auto-escaped by FastAPI's
    # default JSON encoder, so the only way they should disappear is via the
    # server-side strip.)
    assert "<" not in body, "angle brackets in /api/vendors JSON"
    assert ">" not in body
