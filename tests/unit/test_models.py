"""Unit tests for models.py — defaults, JSON roundtrip, hash-only phone storage."""

import hashlib
import json
from datetime import datetime

from sqlmodel import Session, select

from models import CheckIn, Vendor, VendorProfile


def _make_vendor(**overrides):
    base = dict(
        vendor_name_thai="ร้านทดสอบ",
        vendor_name_en="Test Stall",
        owner_name="Test Owner",
        thai_food_price="ผัดไทย 60",
        thai_location="Silom",
        thai_hours="17:00–23:00",
        thai_payment="Cash",
        thai_story="A story",
        location_thai="Silom thai",
        location_display="Silom English",
        phone_hash=hashlib.sha256(b"0812345678").hexdigest(),
    )
    base.update(overrides)
    return Vendor(**base)


def test_vendor_defaults(session: Session):
    v = _make_vendor()
    session.add(v)
    session.commit()
    session.refresh(v)

    assert v.id is not None
    assert v.menu_items == "[]"
    assert v.checkin_count == 0
    assert v.unique_visitors == 0
    assert v.repeat_visitors == 0
    assert v.is_active is True
    assert v.photo_url is None
    assert isinstance(v.created_at, datetime)


def test_vendor_phone_hash_is_sha256_hex(session: Session):
    raw = "0812345678"
    v = _make_vendor(phone_hash=hashlib.sha256(raw.encode()).hexdigest())
    session.add(v)
    session.commit()
    session.refresh(v)

    # Hash never equals raw, always 64 hex chars.
    assert v.phone_hash != raw
    assert len(v.phone_hash) == 64
    assert all(c in "0123456789abcdef" for c in v.phone_hash)


def test_menu_items_json_roundtrip(session: Session):
    menu = [
        {"thai": "ผัดไทย", "english": "Pad Thai", "price": 60},
        {"thai": "ข้าวมันไก่", "english": "Chicken Rice", "price": 55},
    ]
    v = _make_vendor(menu_items=json.dumps(menu))
    session.add(v)
    session.commit()
    session.refresh(v)

    decoded = json.loads(v.menu_items)
    assert decoded == menu
    assert decoded[0]["thai"] == "ผัดไทย"


def test_vendor_profile_links_to_vendor(session: Session):
    v = _make_vendor()
    session.add(v)
    session.commit()
    session.refresh(v)

    session.add(VendorProfile(vendor_id=v.id, language_code="en", profile_text="Hello"))
    session.add(VendorProfile(vendor_id=v.id, language_code="th", profile_text="สวัสดี"))
    session.commit()

    profiles = session.exec(select(VendorProfile).where(VendorProfile.vendor_id == v.id)).all()
    by_code = {p.language_code: p.profile_text for p in profiles}
    assert by_code == {"en": "Hello", "th": "สวัสดี"}


def test_checkin_stores_hash_not_raw_phone(session: Session):
    v = _make_vendor()
    session.add(v)
    session.commit()
    session.refresh(v)

    raw_phone = "0898765432"
    visitor_hash = hashlib.sha256(raw_phone.encode()).hexdigest()
    c = CheckIn(
        vendor_id=v.id,
        visitor_hash=visitor_hash,
        visitor_name="Alex",
        note="Loved it",
        device_language="en",
    )
    session.add(c)
    session.commit()
    session.refresh(c)

    assert c.visitor_hash == visitor_hash
    assert raw_phone not in c.visitor_hash
    assert len(c.visitor_hash) == 64


def test_checkin_optional_fields_default_none(session: Session):
    v = _make_vendor()
    session.add(v)
    session.commit()
    session.refresh(v)

    c = CheckIn(
        vendor_id=v.id,
        visitor_hash="abc" * 21 + "a",  # 64 chars
        visitor_name="NoNote",
    )
    session.add(c)
    session.commit()
    session.refresh(c)

    assert c.note is None
    assert c.device_language is None
    assert isinstance(c.created_at, datetime)
