"""Route: GET /vendor/{id} — bilingual microsite."""

from sqlmodel import Session, select

from models import Vendor


def test_microsite_renders_for_seeded_vendor(client, engine):
    with Session(engine) as s:
        first = s.exec(select(Vendor)).first()
    r = client.get(f"/vendor/{first.id}")
    assert r.status_code == 200
    assert first.vendor_name_en in r.text or first.vendor_name_thai in r.text


def test_microsite_404_for_unknown(client):
    r = client.get("/vendor/99999")
    assert r.status_code == 404


def test_microsite_includes_menu_items(client, engine):
    with Session(engine) as s:
        first = s.exec(select(Vendor)).first()
    r = client.get(f"/vendor/{first.id}")
    # Pad Thai seed menu has these strings.
    assert r.status_code == 200
    # At least one menu item english name should appear in the markup.
    assert "Pad Thai" in r.text or "Chicken" in r.text or "Som Tam" in r.text
