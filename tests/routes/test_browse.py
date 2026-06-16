"""Tests for GET /vendors and GET /api/vendors."""
from sqlmodel import Session

from models import Vendor


def test_browse_page_renders(client):
    r = client.get("/vendors")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_api_vendors_returns_active_vendors(client):
    r = client.get("/api/vendors")
    assert r.status_code == 200
    data = r.json()
    # lifespan seeds 3 vendors
    assert len(data) == 3
    assert {"id", "vendor_name_thai", "vendor_name_en", "location_display",
            "checkin_count", "first_item", "photo_url"} <= set(data[0])


def test_api_vendors_includes_first_menu_item(client):
    data = client.get("/api/vendors").json()
    pad_thai = next(v for v in data if v["vendor_name_en"] == "Auntie Noi's Pad Thai")
    assert pad_thai["first_item"] == "Fresh prawn pad thai"


def test_api_vendors_excludes_inactive(client, engine):
    with Session(engine) as s:
        v = s.get(Vendor, 1)
        v.is_active = False
        s.add(v)
        s.commit()
    data = client.get("/api/vendors").json()
    ids = {v["id"] for v in data}
    assert 1 not in ids
    assert len(data) == 2
