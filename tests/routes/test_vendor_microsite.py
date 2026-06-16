"""Tests for GET /vendor/{id} (microsite)."""


def test_microsite_renders_for_seeded_vendor(client):
    r = client.get("/vendor/1")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Auntie Noi" in r.text


def test_microsite_includes_menu_items(client):
    r = client.get("/vendor/1")
    assert "Fresh prawn pad thai" in r.text


def test_microsite_404_for_unknown(client):
    r = client.get("/vendor/99999")
    assert r.status_code == 404
