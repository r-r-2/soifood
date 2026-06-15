"""Opt-in live smoke tests — hit the real Gemini API.

These are skipped by default (pytest.ini has `addopts = -m "not live"`).
Run with:  pytest -m live  tests/fixtures/live_smoke.py

Requires a real GEMINI_API_KEY in the environment. Each test asserts only
the SHAPE of the response, not specific wording — the actual model output
is non-deterministic.
"""

import os

import pytest

# Skip the whole module if no real key is set — placeholder "test-key" from
# conftest doesn't count.
_LIVE_KEY = os.environ.get("GEMINI_API_KEY", "")
pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not _LIVE_KEY or _LIVE_KEY == "test-key",
        reason="set a real GEMINI_API_KEY to run live smoke tests",
    ),
]


@pytest.fixture
def vendor_data():
    return {
        "q1": "ร้านป้าน้อย / ป้าน้อย สมใจ",
        "q2": "ผัดไทยกุ้งสด 60 บาท, ผัดไทยไก่ 50 บาท",
        "q3": "ตลาดนัดสีลม ใกล้ BTS ศาลาแดง ทางออก 2",
        "q4": "ทุกวัน 17:00–23:00",
        "q5": "เงินสด และ PromptPay",
        "q6": "ทำผัดไทยมาตั้งแต่อายุ 18 ปี",
    }


def test_live_generate_thai_summary(vendor_data):
    import ai
    out = ai.generate_thai_summary(vendor_data)
    assert isinstance(out, str)
    assert len(out) > 30


def test_live_generate_english_profile(vendor_data):
    import ai
    thai = ai.generate_thai_summary(vendor_data)
    out = ai.generate_english_profile(vendor_data, thai)
    assert isinstance(out, str)
    assert len(out) > 30


def test_live_extract_vendor_names(vendor_data):
    import ai
    out = ai.extract_vendor_names(vendor_data["q1"], vendor_data["q3"])
    assert isinstance(out, dict)
    assert "vendor_name_en" in out
    assert "location_display" in out
    assert isinstance(out["vendor_name_en"], str) and out["vendor_name_en"]
    assert isinstance(out["location_display"], str) and out["location_display"]


def test_live_parse_menu_items(vendor_data):
    import ai
    items = ai.parse_menu_items(vendor_data["q2"])
    assert isinstance(items, list)
    assert items, "expected at least one menu item"
    for item in items:
        assert set(item.keys()) >= {"thai", "english", "price"}
        assert isinstance(item["price"], int)


def test_live_generate_profile_for_language():
    import ai

    class FakeVendor:
        vendor_name_en = "Auntie Noi's Pad Thai"
        location_display = "Silom Night Market"
        thai_hours = "17:00–23:00"
        thai_payment = "Cash"

    lang = {"code": "ja", "label": "日本語", "gemini_instruction": "Write in Japanese"}
    out = ai.generate_profile_for_language(FakeVendor(), lang)
    assert isinstance(out, str)
    assert len(out) > 20


def test_live_update_living_portrait():
    import ai
    out = ai.update_living_portrait(
        existing_profile="Auntie Noi serves great pad thai in Silom.",
        new_note="The prawn pad thai was unforgettable.",
        visitor_name="Alex",
        checkin_count=42,
    )
    assert isinstance(out, str)
    assert len(out) > 30
