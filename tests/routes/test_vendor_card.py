"""Route: GET /vendor/{id}/card — printable QR card page."""

from sqlmodel import Session, select

from models import Vendor


def test_card_renders(client, engine):
    with Session(engine) as s:
        vid = s.exec(select(Vendor)).first().id
    r = client.get(f"/vendor/{vid}/card")
    assert r.status_code == 200
    # Card embeds a QR pointing at the vendor URL.
    assert f"/vendor/{vid}" in r.text or f"/qr/{vid}" in r.text


def test_card_404_for_unknown(client):
    r = client.get("/vendor/99999/card")
    assert r.status_code == 404
