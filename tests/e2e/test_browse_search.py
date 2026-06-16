"""E2E: browse page client-side location search."""
import pytest

pytestmark = pytest.mark.e2e


def test_search_filters_vendor_cards(page, live_server):
    page.goto(f"{live_server}/vendors")

    # Cards are rendered client-side from /api/vendors.
    page.wait_for_selector("#cards .vendor-card")
    initial = page.locator("#cards .vendor-card").count()
    assert initial >= 2

    # Search for a term that matches only one seeded vendor's location.
    page.fill("#search", "Ari")
    page.wait_for_function(
        "n => document.querySelectorAll('#cards .vendor-card').length < n",
        arg=initial,
    )
    filtered = page.locator("#cards .vendor-card").count()
    assert 0 < filtered < initial
    assert page.locator("text=Mae Daeng").count() > 0
