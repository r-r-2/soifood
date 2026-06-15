"""Routes: GET /vendors (HTML browse page) and GET /api/vendors (JSON list)."""

from sqlmodel import Session, select

from models import Vendor


def test_browse_page_renders(client):
    r = client.get("/vendors")
    assert r.status_code == 200


def test_api_vendors_returns_active_vendors(client):
    r = client.get("/api/vendors")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) == 3  # 3 seeds

    first = body[0]
    assert {"id", "vendor_name_thai", "vendor_name_en", "location_display",
            "checkin_count", "first_item", "photo_url"} <= set(first.keys())


def test_api_vendors_includes_first_menu_item(client):
    r = client.get("/api/vendors")
    body = r.json()
    by_name = {v["vendor_name_en"]: v for v in body}
    pad_thai = by_name["Auntie Noi's Pad Thai"]
    assert "Fresh prawn pad thai" in pad_thai["first_item"]


def test_api_vendors_excludes_inactive(client, engine):
    with Session(engine) as s:
        first = s.exec(select(Vendor)).first()
        deactivated_id = first.id
        first.is_active = False
        s.add(first)
        s.commit()

    r = client.get("/api/vendors")
    body = r.json()
    ids = [v["id"] for v in body]
    assert deactivated_id not in ids
    assert len(body) == 2
