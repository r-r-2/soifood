"""E2E: vendor onboarding — fill 6 Thai answers + double-entry phone → microsite."""

import pytest

pytestmark = pytest.mark.e2e


def test_full_onboarding_flow_lands_on_microsite(page_mobile, live_server):
    page = page_mobile
    page.goto(f"{live_server}/")

    page.fill("#q1", "ร้านป้าน้อย / ป้าน้อย")
    page.fill("#q2", "ผัดไทยกุ้งสด 60 บาท")
    page.fill("#q3", "ตลาดสีลม ใกล้ BTS ศาลาแดง")
    page.fill("#q4", "ทุกวัน 17:00–23:00")
    page.fill("#q5", "เงินสด, PromptPay")
    page.fill("#q6", "สูตรแม่ ทำมา 20 ปี")

    page.fill("#phone1", "0812345678")
    page.fill("#phone2", "0812345678")

    page.click("#submit-btn")

    # The form's onsubmit hashes the phone then posts; server returns 303 to /vendor/{id}.
    page.wait_for_url("**/vendor/**", timeout=15_000)
    assert "/vendor/" in page.url

    # Microsite renders the stubbed English profile.
    page.wait_for_selector("#profile-text")
    body = page.locator("body").inner_text()
    assert "E2E English profile" in body or "E2E Test Stall" in body


def test_mismatched_phone_shows_error(page_mobile, live_server):
    page = page_mobile
    page.goto(f"{live_server}/")

    page.fill("#q1", "X")
    page.fill("#q2", "X")
    page.fill("#q3", "X")
    page.fill("#q4", "X")
    page.fill("#q5", "X")
    page.fill("#q6", "X")
    page.fill("#phone1", "0811111111")
    page.fill("#phone2", "0822222222")

    page.click("#submit-btn")

    # Error reveals; URL must NOT advance to /vendor/.
    page.wait_for_selector("#phone-error:not(.hidden)", timeout=3_000)
    assert "/vendor/" not in page.url
