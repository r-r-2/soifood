"""E2E: vendor onboarding form."""
import pytest

pytestmark = pytest.mark.e2e


def _fill_questions(page):
    page.fill("#q1", "ร้านป้าน้อย ป้าน้อย สมใจ")
    page.fill("#q2", "ผัดไทยกุ้งสด 60 บาท")
    page.fill("#q3", "ตลาดนัดสีลม ใกล้ BTS ศาลาแดง")
    page.fill("#q4", "ทุกวัน 17:00–23:00")
    page.fill("#q5", "เงินสด และ PromptPay")
    page.fill("#q6", "ทำผัดไทยมาตั้งแต่อายุ 18")


def test_full_onboarding_flow_lands_on_microsite(page, live_server):
    page.goto(f"{live_server}/")
    _fill_questions(page)
    page.fill("#phone1", "0812345678")
    page.fill("#phone2", "0812345678")
    page.click("#submit-btn")

    # Server redirects to /vendor/{id}; AI is stubbed to "E2E Test Stall".
    page.wait_for_url("**/vendor/**")
    assert "/vendor/" in page.url
    assert page.locator("text=E2E Test Stall").count() > 0


def test_mismatched_phone_shows_error(page, live_server):
    page.goto(f"{live_server}/")
    _fill_questions(page)
    page.fill("#phone1", "0812345678")
    page.fill("#phone2", "0899999999")
    page.click("#submit-btn")

    # Client-side validation blocks submit and reveals the error message.
    page.wait_for_selector("#phone-error:not(.hidden)")
    assert "/vendor/" not in page.url
