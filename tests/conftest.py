"""Shared test fixtures.

The app creates its SQLAlchemy engine at import time bound to the real
Postgres ``DATABASE_URL``. For tests we swap ``main.engine`` for a shared
in-memory SQLite engine and mock every Gemini call so the suite is fast,
deterministic, offline, and needs no API key.
"""
import json
from unittest.mock import patch

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


@pytest.fixture
def engine():
    """Fresh in-memory SQLite engine, isolated per test.

    StaticPool keeps a single underlying connection so the in-memory
    database persists across the multiple sessions a request opens.
    """
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture(autouse=True)
def _patch_engine(engine):
    """Point the app's module-level engine at the test SQLite engine."""
    import main

    original = main.engine
    main.engine = engine
    yield
    main.engine = original


@pytest.fixture(autouse=True)
def _mock_ai(request):
    """Replace every AI function with a deterministic stub.

    Patched on ``main`` (where they are imported by name) and on ``ai``
    (for direct unit tests). ``ai._ask`` is also patched as a backstop so
    no test can ever reach the network.

    A test marked ``@pytest.mark.no_ai_mock`` opts out (used to test the
    real ``ai._ask`` wiring with the Gemini client mocked instead).
    """
    if request.node.get_closest_marker("no_ai_mock"):
        yield
        return
    with patch("ai._ask", return_value="stub-ai-text"), \
         patch("main.extract_vendor_names",
               return_value={"vendor_name_en": "Test Stall",
                             "location_display": "Test Market, near BTS Test"}), \
         patch("main.parse_menu_items",
               return_value=[{"thai": "ผัดไทย", "english": "Pad Thai", "price": 60}]), \
         patch("main.generate_thai_summary", return_value="สรุปภาษาไทย"), \
         patch("main.generate_english_profile", return_value="A warm English profile."), \
         patch("main.generate_profile_for_language", return_value="Generated profile."):
        yield


@pytest.fixture
def client():
    """FastAPI TestClient. Lifespan runs against the SQLite engine and
    seeds it (see ``seed_vendors`` for the seeded-DB variant)."""
    from fastapi.testclient import TestClient

    import main

    with TestClient(main.app) as c:
        yield c


@pytest.fixture
def db_session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def make_vendor(engine):
    """Factory: insert a Vendor (+ optional en/th profiles) and return it."""
    import hashlib

    from models import Vendor, VendorProfile

    def _make(**overrides):
        defaults = dict(
            vendor_name_thai="ร้านทดสอบ",
            vendor_name_en="Test Stall",
            owner_name="ทดสอบ เจ้าของ",
            thai_food_price="ผัดไทย 60 บาท",
            thai_location="ตลาดทดสอบ",
            thai_hours="ทุกวัน 17:00–23:00",
            thai_payment="เงินสด",
            thai_story="เรื่องราวทดสอบ",
            location_thai="ตลาดทดสอบ",
            location_display="Test Market, near BTS Test",
            menu_items=json.dumps(
                [{"thai": "ผัดไทย", "english": "Pad Thai", "price": 60}]
            ),
            phone_hash=hashlib.sha256(b"test-vendor").hexdigest(),
        )
        defaults.update(overrides)
        with Session(engine) as session:
            vendor = Vendor(**defaults)
            session.add(vendor)
            session.flush()
            session.add(VendorProfile(vendor_id=vendor.id, language_code="en",
                                      profile_text="A warm English profile."))
            session.add(VendorProfile(vendor_id=vendor.id, language_code="th",
                                      profile_text="สรุปภาษาไทย"))
            session.commit()
            session.refresh(vendor)
            session.expunge(vendor)
            return vendor

    return _make
