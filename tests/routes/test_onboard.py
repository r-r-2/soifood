"""Routes: GET / and POST /onboard."""

import hashlib
import json

from sqlmodel import Session, select

from models import Vendor, VendorProfile
from tests.fixtures import ai_responses, vendor_data


def test_get_onboard_form_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    # Onboarding is in Thai — must have the first question marker.
    assert "ชื่อร้าน" in r.text or "soifood" in r.text


def test_post_onboard_creates_vendor_and_two_profiles(client, engine):
    payload = {
        **vendor_data.PAD_THAI,
        "phone_hash": hashlib.sha256(b"0812345678").hexdigest(),
    }

    r = client.post("/onboard", data=payload, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"].startswith("/vendor/")

    new_id = int(r.headers["location"].rsplit("/", 1)[-1])

    with Session(engine) as s:
        v = s.get(Vendor, new_id)
        assert v is not None
        assert v.vendor_name_en == ai_responses.VENDOR_NAMES["vendor_name_en"]
        assert v.location_display == ai_responses.VENDOR_NAMES["location_display"]
        assert v.thai_food_price == vendor_data.PAD_THAI["q2"]
        assert v.phone_hash == payload["phone_hash"]

        menu = json.loads(v.menu_items)
        assert menu == ai_responses.MENU_ITEMS

        profiles = s.exec(
            select(VendorProfile).where(VendorProfile.vendor_id == new_id)
        ).all()
        by_code = {p.language_code: p.profile_text for p in profiles}
        assert by_code["th"] == ai_responses.THAI_SUMMARY
        assert by_code["en"] == ai_responses.ENGLISH_PROFILE


def test_post_onboard_missing_field_returns_422(client):
    payload = {**vendor_data.PAD_THAI}  # no phone_hash
    r = client.post("/onboard", data=payload)
    assert r.status_code == 422
