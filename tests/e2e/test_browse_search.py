"""E2E: browse page — client-side filtering narrows the vendor list."""

import pytest

pytestmark = pytest.mark.e2e


def test_search_filters_vendor_cards(page_mobile, live_server):
    page = page_mobile
    page.goto(f"{live_server}/vendors")
    page.wait_for_selector("#cards:not(.hidden)", timeout=10_000)

    cards_locator = page.locator("#cards > *")
    # 3 seed vendors load by default.
    page.wait_for_function("document.querySelectorAll('#cards > *').length === 3", timeout=10_000)
    assert cards_locator.count() == 3

    # Typing "Silom" should narrow to the Pad Thai seed.
    page.fill("#search", "Silom")
    page.wait_for_function(
        "document.querySelectorAll('#cards > *').length < 3", timeout=5_000
    )
    visible_text = page.locator("#cards").inner_text()
    assert "Pad Thai" in visible_text or "Silom" in visible_text
