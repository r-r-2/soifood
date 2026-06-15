"""Route: POST /checkin/{id} — unique/repeat tracking + living portrait update."""

import hashlib

from sqlmodel import Session, select

from models import CheckIn, Vendor, VendorProfile
from tests.fixtures import ai_responses


def _first_vendor_id(engine):
    with Session(engine) as s:
        return s.exec(select(Vendor)).first().id


def _hash(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()


def test_checkin_new_visitor_increments_unique(client, engine):
    vid = _first_vendor_id(engine)
    with Session(engine) as s:
        before = s.get(Vendor, vid)
        before_count = before.checkin_count
        before_unique = before.unique_visitors

    r = client.post(
        f"/checkin/{vid}",
        data={"visitor_hash": _hash("0811111111"), "visitor_name": "Alex"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["points"] == 10
    assert body["total_checkins"] == before_count + 1

    with Session(engine) as s:
        v = s.get(Vendor, vid)
        assert v.checkin_count == before_count + 1
        assert v.unique_visitors == before_unique + 1


def test_checkin_repeat_visitor_increments_repeat(client, engine):
    vid = _first_vendor_id(engine)
    visitor_hash = _hash("0822222222")

    client.post(
        f"/checkin/{vid}",
        data={"visitor_hash": visitor_hash, "visitor_name": "Sam"},
    )
    with Session(engine) as s:
        mid = s.get(Vendor, vid)
        unique_after_first = mid.unique_visitors
        repeat_before = mid.repeat_visitors

    r = client.post(
        f"/checkin/{vid}",
        data={"visitor_hash": visitor_hash, "visitor_name": "Sam"},
    )
    assert r.status_code == 200

    with Session(engine) as s:
        v = s.get(Vendor, vid)
        assert v.unique_visitors == unique_after_first  # unchanged
        assert v.repeat_visitors == repeat_before + 1


def test_checkin_with_note_updates_english_profile(client, engine):
    vid = _first_vendor_id(engine)
    with Session(engine) as s:
        before = s.exec(
            select(VendorProfile)
            .where(VendorProfile.vendor_id == vid)
            .where(VendorProfile.language_code == "en")
        ).first()
        before_text = before.profile_text

    r = client.post(
        f"/checkin/{vid}",
        data={
            "visitor_hash": _hash("0833333333"),
            "visitor_name": "Jamie",
            "note": "Best pad thai I have had in Bangkok",
        },
    )
    assert r.status_code == 200

    with Session(engine) as s:
        after = s.exec(
            select(VendorProfile)
            .where(VendorProfile.vendor_id == vid)
            .where(VendorProfile.language_code == "en")
        ).first()
        assert after.profile_text == ai_responses.UPDATED_PORTRAIT
        assert after.profile_text != before_text


def test_checkin_without_note_does_not_update_profile(client, engine):
    vid = _first_vendor_id(engine)
    with Session(engine) as s:
        before = s.exec(
            select(VendorProfile)
            .where(VendorProfile.vendor_id == vid)
            .where(VendorProfile.language_code == "en")
        ).first()
        before_text = before.profile_text

    r = client.post(
        f"/checkin/{vid}",
        data={"visitor_hash": _hash("0844444444"), "visitor_name": "Pat"},
    )
    assert r.status_code == 200

    with Session(engine) as s:
        after = s.exec(
            select(VendorProfile)
            .where(VendorProfile.vendor_id == vid)
            .where(VendorProfile.language_code == "en")
        ).first()
        assert after.profile_text == before_text


def test_checkin_empty_note_does_not_update_profile(client, engine):
    vid = _first_vendor_id(engine)
    with Session(engine) as s:
        before = s.exec(
            select(VendorProfile)
            .where(VendorProfile.vendor_id == vid)
            .where(VendorProfile.language_code == "en")
        ).first()
        before_text = before.profile_text

    client.post(
        f"/checkin/{vid}",
        data={
            "visitor_hash": _hash("0855555555"),
            "visitor_name": "X",
            "note": "   ",
        },
    )

    with Session(engine) as s:
        after = s.exec(
            select(VendorProfile)
            .where(VendorProfile.vendor_id == vid)
            .where(VendorProfile.language_code == "en")
        ).first()
        assert after.profile_text == before_text


def test_checkin_persists_checkin_row(client, engine):
    vid = _first_vendor_id(engine)
    visitor_hash = _hash("0866666666")
    client.post(
        f"/checkin/{vid}",
        data={
            "visitor_hash": visitor_hash,
            "visitor_name": "Riley",
            "note": "Yum",
            "device_language": "ja",
        },
    )

    with Session(engine) as s:
        row = s.exec(
            select(CheckIn)
            .where(CheckIn.vendor_id == vid)
            .where(CheckIn.visitor_hash == visitor_hash)
        ).first()
        assert row is not None
        assert row.visitor_name == "Riley"
        assert row.note == "Yum"
        assert row.device_language == "ja"


def test_checkin_404_for_unknown_vendor(client):
    r = client.post(
        "/checkin/99999",
        data={"visitor_hash": _hash("0877777777"), "visitor_name": "Z"},
    )
    assert r.status_code == 404
    assert "not found" in r.json()["error"].lower()
