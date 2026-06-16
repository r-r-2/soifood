"""Tests for GET /leaderboard."""
from sqlmodel import Session

from models import CheckIn


def test_leaderboard_renders_empty(client):
    # No check-ins seeded by default.
    r = client.get("/leaderboard")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_leaderboard_aggregates_points_and_vendors(client, engine):
    with Session(engine) as s:
        # Alex: 2 check-ins across 2 vendors -> 20 points, 2 vendors
        s.add(CheckIn(vendor_id=1, visitor_hash="alex", visitor_name="Alex"))
        s.add(CheckIn(vendor_id=2, visitor_hash="alex", visitor_name="Alex"))
        # Sam: 1 check-in -> 10 points, 1 vendor
        s.add(CheckIn(vendor_id=1, visitor_hash="sam", visitor_name="Sam"))
        s.commit()

    r = client.get("/leaderboard")
    assert r.status_code == 200
    body = r.text
    # Alex (20 pts) should rank above Sam (10 pts)
    assert body.index("Alex") < body.index("Sam")
    assert "20" in body


def test_leaderboard_caps_at_twenty(client, engine):
    # 25 distinct visitors, each with a unique point total so ordering is
    # deterministic and the rendered board is exactly the top 20.
    with Session(engine) as s:
        for i in range(25):
            for _ in range(i + 1):  # Visitor i has i+1 check-ins
                s.add(CheckIn(vendor_id=1, visitor_hash=f"v{i}",
                              visitor_name=f"Visitor{i}"))
        s.commit()

    html = client.get("/leaderboard").text
    rendered = {f"Visitor{i}" for i in range(25) if f"Visitor{i}<" in html}
    assert len(rendered) == 20
    # Top scorer present, lowest scorers dropped.
    assert "Visitor24" in rendered
    assert "Visitor0" not in rendered
