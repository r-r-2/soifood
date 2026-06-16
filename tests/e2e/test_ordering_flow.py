"""E2E: frontend-only ordering (cart + order card overlay)."""
import pytest

pytestmark = pytest.mark.e2e


def test_add_items_updates_cart_and_opens_order_card(page, live_server):
    page.goto(f"{live_server}/vendor/1")

    # Add two of the first menu item via its "+" qty button.
    plus = page.locator(".menu-item").first.locator("button:has-text('+')")
    plus.click()
    plus.click()
    assert page.locator("#qty-0").inner_text() == "2"

    # Cart bar appears and reflects the items.
    page.wait_for_selector("#cart-bar.visible")
    assert "2 item" in page.locator("#cart-summary").inner_text()

    # Tapping the cart bar opens the full-screen order card.
    page.click("#cart-bar")
    page.wait_for_selector("#order-overlay")
    assert page.locator("#order-items").count() > 0
    # Total should be non-zero (2 × ฿60 = ฿120).
    assert "120" in page.locator("#order-total").inner_text()
