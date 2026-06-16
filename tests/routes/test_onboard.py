"""Tests for GET / (form) and POST /onboard."""
from sqlmodel import Session, select

from models import Vendor, VendorProfile


def test_get_onboard_form_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_post_onboard_creates_vendor_and_two_profiles(client, engine):
    r = client.post("/onboard", data={
        "q1": "ร้านป้าน้อย ป้าน้อย",
        "q2": "ผัดไทย 60 บาท",
        "q3": "ตลาดสีลม",
        "q4": "ทุกวัน 17:00–23:00",
        "q5": "เงินสด",
        "q6": "เรื่องราว",
        "phone_hash": "a" * 64,
    }, follow_redirects=False)

    assert r.status_code == 303
    location = r.headers["location"]
    assert location.startswith("/vendor/")

    new_id = int(location.rsplit("/", 1)[1])
    with Session(engine) as s:
        vendor = s.get(Vendor, new_id)
        assert vendor is not None
        # AI stubs (see conftest) supply the extracted fields
        assert vendor.vendor_name_en == "Test Stall"
        assert vendor.location_display == "Test Market, near BTS Test"
        assert vendor.phone_hash == "a" * 64

        profiles = s.exec(
            select(VendorProfile).where(VendorProfile.vendor_id == new_id)
        ).all()
        langs = {p.language_code for p in profiles}
    assert langs == {"en", "th"}


def test_post_onboard_missing_field_returns_422(client):
    r = client.post("/onboard", data={
        "q1": "ร้าน", "q2": "ผัดไทย",  # q3..q6 + phone_hash missing
    })
    assert r.status_code == 422
