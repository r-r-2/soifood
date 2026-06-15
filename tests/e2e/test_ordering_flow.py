"""E2E: ordering — add menu items, open order card, verify total + Thai audio button."""

import pytest

pytestmark = pytest.mark.e2e


def test_add_items_updates_cart_and_opens_order_card(page_mobile, live_server):
    page = page_mobile
    # Vendor 1 is a seed — Pad Thai stall.
    page.goto(f"{live_server}/vendor/1")
    page.wait_for_selector("#menu-list")

    # Increment item 0 twice (60 baht × 2 = 120).
    page.locator(".menu-item[data-idx='0'] .qty-btn").nth(1).click()
    page.locator(".menu-item[data-idx='0'] .qty-btn").nth(1).click()

    cart = page.locator("#cart-summary")
    cart.wait_for(state="visible")
    summary = cart.inner_text()
    assert "2" in summary
    assert "120" in summary

    page.click("#cart-bar")
    page.wait_for_selector("#order-overlay", state="visible")

    total = page.locator("#order-total").inner_text()
    assert "120" in total

    # 🔊 audio button is present and tappable.
    audio = page.locator("#audio-btn")
    assert audio.is_visible()
