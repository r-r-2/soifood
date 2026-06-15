"""E2E: visitor check-in — open modal, submit name + phone + note, see success."""

import pytest

pytestmark = pytest.mark.e2e


def test_checkin_succeeds_and_awards_points(page_mobile, live_server):
    page = page_mobile
    page.goto(f"{live_server}/vendor/2")  # Khao Man Gai seed
    page.wait_for_selector("#menu-list")

    # The visible CTA reads "I've been here · +10 pts" and toggles the modal.
    page.locator("button[onclick='openCheckin()']").click()
    page.wait_for_selector("#checkin-modal", state="visible")

    page.fill("#ci-name", "Alex Tester")
    page.fill("#ci-phone", "0899999999")
    page.fill("#ci-note", "Best chicken rice in Bangkok")

    # Modal submit — scoped to the modal so it can't collide with the page CTA.
    page.locator("#checkin-modal button[onclick='submitCheckin()']").click()

    # Success panel reveals after the POST returns.
    page.wait_for_selector("#checkin-success:not(.hidden)", timeout=10_000)
