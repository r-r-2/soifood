"""Tests for GET /vendor/{id}/card (printable QR card)."""


def test_card_renders(client):
    r = client.get("/vendor/1/card")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_card_404_for_unknown(client):
    r = client.get("/vendor/99999/card")
    assert r.status_code == 404
