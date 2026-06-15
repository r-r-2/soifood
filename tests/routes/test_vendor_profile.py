"""Route: GET /vendor/{id}/profile?lang=XX — cache-aside multilingual profiles."""

from sqlmodel import Session, select

from models import Vendor, VendorProfile
from tests.fixtures import ai_responses


def _first_vendor_id(engine):
    with Session(engine) as s:
        return s.exec(select(Vendor)).first().id


def test_profile_cache_hit_returns_existing(client, engine):
    vid = _first_vendor_id(engine)
    # Seed data inserts en + th profiles.
    r = client.get(f"/vendor/{vid}/profile?lang=en")
    assert r.status_code == 200
    body = r.json()
    assert "profile_text" in body
    assert len(body["profile_text"]) > 20  # real prose


def test_profile_cache_miss_generates_and_persists(client, engine):
    vid = _first_vendor_id(engine)
    # ja not generated on onboard — first request is a miss.
    r = client.get(f"/vendor/{vid}/profile?lang=ja")
    assert r.status_code == 200
    assert r.json()["profile_text"] == ai_responses.JA_PROFILE

    # Persisted — second request reads from DB without regenerating.
    with Session(engine) as s:
        row = s.exec(
            select(VendorProfile)
            .where(VendorProfile.vendor_id == vid)
            .where(VendorProfile.language_code == "ja")
        ).first()
        assert row is not None
        assert row.profile_text == ai_responses.JA_PROFILE


def test_profile_unsupported_language_returns_400(client, engine):
    vid = _first_vendor_id(engine)
    r = client.get(f"/vendor/{vid}/profile?lang=xx")
    assert r.status_code == 400
    assert "Unsupported" in r.json()["error"]


def test_profile_unknown_vendor_returns_404(client):
    r = client.get("/vendor/99999/profile?lang=en")
    assert r.status_code == 404
    assert "not found" in r.json()["error"].lower()
