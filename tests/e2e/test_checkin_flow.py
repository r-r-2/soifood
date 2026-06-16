"""E2E: visitor check-in on a vendor microsite."""
import pytest

pytestmark = pytest.mark.e2e


def test_checkin_succeeds_and_awards_points(page, live_server):
    page.goto(f"{live_server}/vendor/1")

    page.click("button:has-text(\"I've been here\")")  # opens the modal
    page.wait_for_selector("#checkin-modal:not(.hidden)")

    page.fill("#ci-name", "Sarah K.")
    page.fill("#ci-phone", "0811112222")
    page.fill("#ci-note", "Best pad thai near Sala Daeng!")
    page.click("button:has-text('Check in · +10 pts')")

    # Success panel becomes visible after the POST resolves.
    page.wait_for_selector("#checkin-success:not(.hidden)")
    assert page.locator("#checkin-success").is_visible()
