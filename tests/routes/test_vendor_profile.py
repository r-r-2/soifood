"""Tests for GET /vendor/{id}/profile — lazy cache-aside generation."""
from sqlmodel import Session, select

from models import VendorProfile


def test_profile_cache_hit_returns_existing(client):
    # Seeded vendor 1 already has an 'en' profile.
    r = client.get("/vendor/1/profile?lang=en")
    assert r.status_code == 200
    assert "Auntie Noi" in r.json()["profile_text"]


def test_profile_cache_miss_generates_and_persists(client, engine):
    # 'ja' is not generated on onboard — first request should generate it.
    with Session(engine) as s:
        before = s.exec(
            select(VendorProfile)
            .where(VendorProfile.vendor_id == 1)
            .where(VendorProfile.language_code == "ja")
        ).first()
    assert before is None

    r = client.get("/vendor/1/profile?lang=ja")
    assert r.status_code == 200
    assert r.json()["profile_text"] == "Generated profile."  # AI stub

    with Session(engine) as s:
        after = s.exec(
            select(VendorProfile)
            .where(VendorProfile.vendor_id == 1)
            .where(VendorProfile.language_code == "ja")
        ).first()
    assert after is not None
    assert after.profile_text == "Generated profile."


def test_profile_unknown_vendor_returns_404(client):
    r = client.get("/vendor/99999/profile?lang=en")
    assert r.status_code == 404


def test_profile_unsupported_language_returns_400(client):
    r = client.get("/vendor/1/profile?lang=xx")
    assert r.status_code == 400
