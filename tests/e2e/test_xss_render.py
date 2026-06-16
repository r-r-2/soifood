"""E2E regression: a malicious vendor name must not execute as script on the
public browse page (stored XSS via innerHTML in renderCard)."""
import pytest

pytestmark = pytest.mark.e2e

PAYLOAD = "<img src=x onerror=\"window.__xss_fired=true\">"


def test_vendors_browse_does_not_execute_injected_payload(page, live_server):
    # Onboard a vendor whose Thai name carries an XSS payload (q1 is stored
    # verbatim as vendor_name_thai and reflected into /api/vendors).
    page.goto(f"{live_server}/")
    page.fill("#q1", PAYLOAD)
    page.fill("#q2", "ผัดไทย 60 บาท")
    page.fill("#q3", "ตลาดทดสอบ")
    page.fill("#q4", "ทุกวัน 17:00")
    page.fill("#q5", "เงินสด")
    page.fill("#q6", "เรื่องราว")
    page.fill("#phone1", "0812345678")
    page.fill("#phone2", "0812345678")
    page.click("#submit-btn")
    page.wait_for_url("**/vendor/**")

    # Visit the public browse page where cards render via innerHTML.
    page.goto(f"{live_server}/vendors")
    page.wait_for_selector("#cards .vendor-card")

    # The onerror handler must never have fired...
    assert page.evaluate("window.__xss_fired === true") is False
    # ...and the payload must be present as escaped text, not a live <img>.
    assert page.locator("#cards img[src='x']").count() == 0
    assert page.locator("#cards").get_by_text(PAYLOAD).count() > 0
