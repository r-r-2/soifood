"""Route: GET /leaderboard — community supporter aggregation."""

import hashlib

from sqlmodel import Session

from models import CheckIn


def _hash(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()


def test_leaderboard_renders_empty(empty_client):
    r = empty_client.get("/leaderboard")
    assert r.status_code == 200


def test_leaderboard_aggregates_points_and_vendors(client, engine):
    """3 check-ins from one visitor across 2 vendors → 30 points, 2 vendors."""
    alex = _hash("0811111111")
    sam = _hash("0822222222")

    with Session(engine) as s:
        # Alex: 2 check-ins to vendor 1, 1 to vendor 2 → 30 pts, 2 vendors
        s.add(CheckIn(vendor_id=1, visitor_hash=alex, visitor_name="Alex"))
        s.add(CheckIn(vendor_id=1, visitor_hash=alex, visitor_name="Alex"))
        s.add(CheckIn(vendor_id=2, visitor_hash=alex, visitor_name="Alex"))
        # Sam: 1 check-in to vendor 3 → 10 pts, 1 vendor
        s.add(CheckIn(vendor_id=3, visitor_hash=sam, visitor_name="Sam"))
        s.commit()

    r = client.get("/leaderboard")
    assert r.status_code == 200
    body = r.text
    # Alex outranks Sam.
    assert body.index("Alex") < body.index("Sam")
    # Points appear in rendered HTML.
    assert "30" in body
    assert "10" in body


def test_leaderboard_caps_at_twenty(client, engine):
    """Spawn 25 distinct visitors; only top 20 should render."""
    with Session(engine) as s:
        for i in range(25):
            h = _hash(f"phone-{i:03d}")
            # Give each visitor i+1 check-ins so ranking is deterministic.
            for _ in range(i + 1):
                s.add(CheckIn(vendor_id=1, visitor_hash=h, visitor_name=f"User{i:03d}"))
        s.commit()

    r = client.get("/leaderboard")
    assert r.status_code == 200
    # The 5 lowest-scoring users (User000–User004) should be cut.
    assert "User024" in r.text  # top scorer
    assert "User004" not in r.text  # below cutoff
