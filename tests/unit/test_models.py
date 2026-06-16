"""Unit tests for the SQLModel tables."""
import hashlib
import json

from sqlmodel import Session

from models import CheckIn, Vendor, VendorProfile


def test_vendor_defaults(engine):
    with Session(engine) as s:
        v = Vendor(
            vendor_name_thai="ร้าน", vendor_name_en="Stall", owner_name="Owner",
            thai_food_price="x", thai_location="y", thai_hours="z",
            thai_payment="cash", thai_story="story",
            location_thai="y", location_display="Y",
            phone_hash="hash",
        )
        s.add(v)
        s.commit()
        s.refresh(v)
    assert v.id is not None
    assert v.menu_items == "[]"
    assert v.checkin_count == 0
    assert v.unique_visitors == 0
    assert v.repeat_visitors == 0
    assert v.is_active is True
    assert v.photo_url is None
    assert v.created_at is not None


def test_menu_items_json_roundtrip(engine):
    items = [{"thai": "ผัดไทย", "english": "Pad Thai", "price": 60}]
    with Session(engine) as s:
        v = Vendor(
            vendor_name_thai="ร้าน", vendor_name_en="Stall", owner_name="Owner",
            thai_food_price="x", thai_location="y", thai_hours="z",
            thai_payment="cash", thai_story="story",
            location_thai="y", location_display="Y",
            phone_hash="hash", menu_items=json.dumps(items),
        )
        s.add(v)
        s.commit()
        s.refresh(v)
        loaded = json.loads(v.menu_items)
    assert loaded == items


def test_vendor_phone_hash_is_sha256_hex(engine):
    digest = hashlib.sha256(b"0812345678").hexdigest()
    with Session(engine) as s:
        v = Vendor(
            vendor_name_thai="ร้าน", vendor_name_en="Stall", owner_name="Owner",
            thai_food_price="x", thai_location="y", thai_hours="z",
            thai_payment="cash", thai_story="story",
            location_thai="y", location_display="Y", phone_hash=digest,
        )
        s.add(v)
        s.commit()
        s.refresh(v)
    assert len(v.phone_hash) == 64
    assert v.phone_hash == digest


def test_vendor_profile_links_to_vendor(engine):
    with Session(engine) as s:
        v = Vendor(
            vendor_name_thai="ร้าน", vendor_name_en="Stall", owner_name="Owner",
            thai_food_price="x", thai_location="y", thai_hours="z",
            thai_payment="cash", thai_story="story",
            location_thai="y", location_display="Y", phone_hash="hash",
        )
        s.add(v)
        s.flush()
        vendor_id = v.id
        p = VendorProfile(vendor_id=vendor_id, language_code="en", profile_text="hello")
        s.add(p)
        s.commit()
        s.refresh(p)
        assert p.vendor_id == vendor_id
        assert p.language_code == "en"


def test_checkin_stores_hash_not_raw_phone(engine):
    digest = hashlib.sha256(b"0899999999").hexdigest()
    with Session(engine) as s:
        c = CheckIn(vendor_id=1, visitor_hash=digest, visitor_name="Alex")
        s.add(c)
        s.commit()
        s.refresh(c)
    assert c.visitor_hash == digest
    assert "0899999999" not in c.visitor_hash


def test_checkin_optional_fields_default_none(engine):
    with Session(engine) as s:
        c = CheckIn(vendor_id=1, visitor_hash="h", visitor_name="Alex")
        s.add(c)
        s.commit()
        s.refresh(c)
    assert c.note is None
    assert c.device_language is None
    assert c.created_at is not None
