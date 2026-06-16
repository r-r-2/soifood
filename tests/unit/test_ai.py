"""Unit tests for ai.py. Every test mocks ai._ask so no Gemini call happens."""
from unittest.mock import patch

import pytest

import ai


VENDOR_DATA = {
    "q1": "ร้านป้าน้อย เจ้าของชื่อป้าน้อย",
    "q2": "ผัดไทยกุ้งสด 60 บาท",
    "q3": "ตลาดนัดสีลม ใกล้ BTS ศาลาแดง",
    "q4": "ทุกวัน 17:00–23:00",
    "q5": "เงินสด และ PromptPay",
    "q6": "ทำผัดไทยมาตั้งแต่อายุ 18",
}


@pytest.mark.no_ai_mock
def test_ask_calls_correct_model():
    """_ask must always use gemini-2.5-flash-lite (CLAUDE.md hard rule)."""
    fake_response = type("R", (), {"text": "  hello  "})()
    with patch.object(ai._client.models, "generate_content",
                      return_value=fake_response) as gen:
        out = ai._ask("prompt here")
    assert out == "hello"  # stripped
    assert gen.call_args.kwargs["model"] == "gemini-2.5-flash-lite"
    assert gen.call_args.kwargs["contents"] == "prompt here"


def test_generate_thai_summary_includes_all_six_answers():
    with patch("ai._ask", return_value="summary") as ask:
        ai.generate_thai_summary(VENDOR_DATA)
    prompt = ask.call_args.args[0]
    for key in ("q1", "q2", "q3", "q4", "q5", "q6"):
        assert VENDOR_DATA[key] in prompt


def test_generate_english_profile_includes_thai_summary_and_answers():
    with patch("ai._ask", return_value="profile") as ask:
        ai.generate_english_profile(VENDOR_DATA, "THAI_SUMMARY_TOKEN")
    prompt = ask.call_args.args[0]
    assert "THAI_SUMMARY_TOKEN" in prompt
    assert VENDOR_DATA["q2"] in prompt
    assert "English" in prompt


def test_extract_vendor_names_parses_clean_json():
    with patch("ai._ask",
               return_value='{"vendor_name_en": "Auntie Noi", "location_display": "Silom"}'):
        out = ai.extract_vendor_names("q1", "q3")
    assert out == {"vendor_name_en": "Auntie Noi", "location_display": "Silom"}


def test_extract_vendor_names_strips_markdown_fences():
    fenced = '```json\n{"vendor_name_en": "X", "location_display": "Y"}\n```'
    with patch("ai._ask", return_value=fenced):
        out = ai.extract_vendor_names("q1", "q3")
    assert out["vendor_name_en"] == "X"


def test_extract_vendor_names_strips_bare_backticks():
    with patch("ai._ask",
               return_value='`{"vendor_name_en": "X", "location_display": "Y"}`'):
        out = ai.extract_vendor_names("q1", "q3")
    assert out["location_display"] == "Y"


def test_parse_menu_items_returns_list_of_dicts():
    payload = '[{"thai": "ผัดไทย", "english": "Pad Thai", "price": 60}]'
    with patch("ai._ask", return_value=payload):
        out = ai.parse_menu_items("ผัดไทย 60 บาท")
    assert isinstance(out, list)
    assert out[0]["english"] == "Pad Thai"
    assert out[0]["price"] == 60


def test_parse_menu_items_handles_fenced_response():
    payload = '```json\n[{"thai": "ก", "english": "A", "price": 0}]\n```'
    with patch("ai._ask", return_value=payload):
        out = ai.parse_menu_items("input")
    assert out[0]["price"] == 0


def test_generate_profile_for_language_uses_lang_config():
    vendor = type("V", (), {
        "vendor_name_en": "Test Stall",
        "location_display": "Test Market",
        "thai_hours": "ทุกวัน",
        "thai_payment": "เงินสด",
    })()
    lang_config = {"label": "日本語", "gemini_instruction": "Write in Japanese"}
    with patch("ai._ask", return_value="プロフィール") as ask:
        ai.generate_profile_for_language(vendor, lang_config)
    prompt = ask.call_args.args[0]
    assert "日本語" in prompt
    assert "Write in Japanese" in prompt
    assert "Test Stall" in prompt


def test_update_living_portrait_weaves_in_note():
    with patch("ai._ask", return_value="updated profile") as ask:
        out = ai.update_living_portrait(
            "Existing profile.", "Loved the pad thai!", "Alex", 88)
    prompt = ask.call_args.args[0]
    assert "Existing profile." in prompt
    assert "Loved the pad thai!" in prompt
    assert "Alex" in prompt
    assert "88" in prompt
    assert out == "updated profile"
