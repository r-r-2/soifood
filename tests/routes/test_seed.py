"""Lifespan seeding — verifies the 3 seed vendors appear and re-running is a no-op."""

from sqlmodel import Session, select

from models import Vendor, VendorProfile
from main import seed_data


def test_seed_creates_three_vendors_with_profiles(client, engine):
    with Session(engine) as s:
        vendors = s.exec(select(Vendor)).all()
        assert len(vendors) == 3

        names = {v.vendor_name_en for v in vendors}
        assert names == {
            "Auntie Noi's Pad Thai",
            "Uncle Somchai's Khao Man Gai",
            "Mae Daeng's Isaan Som Tam",
        }

        # Every seed vendor has both en + th profiles.
        for v in vendors:
            profiles = s.exec(
                select(VendorProfile).where(VendorProfile.vendor_id == v.id)
            ).all()
            langs = {p.language_code for p in profiles}
            assert {"en", "th"} <= langs


def test_seed_is_idempotent(client, engine):
    """Running seed_data again on a populated DB must not duplicate rows."""
    with Session(engine) as s:
        before = len(s.exec(select(Vendor)).all())
        seed_data(s)
        after = len(s.exec(select(Vendor)).all())
        assert before == after == 3


def test_seed_phone_hashes_are_sha256(client, engine):
    with Session(engine) as s:
        for v in s.exec(select(Vendor)).all():
            assert len(v.phone_hash) == 64
            assert all(c in "0123456789abcdef" for c in v.phone_hash)
