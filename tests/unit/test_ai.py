"""Unit tests for ai.py — verifies prompt shape, JSON parsing, fence stripping.

The root conftest autouse-patches every ai.py function with canned returns.
We disable that autouse here (via `mock_ai` fixture override) and patch only
`_ask`, so the real generate_* / extract / parse functions are exercised
against a deterministic stub.
"""

import pytest

import ai


@pytest.fixture
def mock_ai():
    """Override the root conftest autouse — leave ai.py functions un-patched."""
    return None


@pytest.fixture
def asks(monkeypatch):
    """Capture every prompt sent to _ask and return scripted responses."""
    captured = []
    responses = iter([])

    def _fake_ask(prompt):
        captured.append(prompt)
        return next(responses)

    monkeypatch.setattr(ai, "_ask", _fake_ask)

    def _set(*replies):
        nonlocal responses
        responses = iter(replies)

    return captured, _set


def test_generate_thai_summary_includes_all_six_answers(asks):
    captured, set_replies = asks
    set_replies("สรุปไทย")

    data = {"q1": "Q1", "q2": "Q2", "q3": "Q3", "q4": "Q4", "q5": "Q5", "q6": "Q6"}
    out = ai.generate_thai_summary(data)

    assert out == "สรุปไทย"
    prompt = captured[0]
    for v in data.values():
        assert v in prompt
    # Confirm prompt steers toward Thai output.
    assert "ภาษาไทย" in prompt


def test_generate_english_profile_includes_thai_summary_and_answers(asks):
    captured, set_replies = asks
    set_replies("English profile out")

    data = {"q1": "A", "q2": "B", "q3": "C", "q4": "D", "q5": "E", "q6": "F"}
    out = ai.generate_english_profile(data, thai_summary="THAI-REF")

    assert out == "English profile out"
    prompt = captured[0]
    assert "THAI-REF" in prompt
    for v in data.values():
        assert v in prompt
    assert "English" in prompt


def test_extract_vendor_names_parses_clean_json(asks):
    _, set_replies = asks
    set_replies('{"vendor_name_en": "Auntie Noi", "location_display": "Silom"}')

    result = ai.extract_vendor_names("Q1 thai", "Q3 thai")
    assert result == {"vendor_name_en": "Auntie Noi", "location_display": "Silom"}


def test_extract_vendor_names_strips_markdown_fences(asks):
    _, set_replies = asks
    set_replies(
        '```json\n{"vendor_name_en": "Noi", "location_display": "Silom"}\n```'
    )

    result = ai.extract_vendor_names("q1", "q3")
    assert result["vendor_name_en"] == "Noi"
    assert result["location_display"] == "Silom"


def test_extract_vendor_names_strips_bare_backticks(asks):
    _, set_replies = asks
    set_replies('`{"vendor_name_en": "X", "location_display": "Y"}`')

    result = ai.extract_vendor_names("q1", "q3")
    assert result == {"vendor_name_en": "X", "location_display": "Y"}


def test_parse_menu_items_returns_list_of_dicts(asks):
    _, set_replies = asks
    set_replies(
        '[{"thai": "ผัดไทย", "english": "Pad Thai", "price": 60}, '
        '{"thai": "ข้าวมันไก่", "english": "Chicken Rice", "price": 55}]'
    )

    items = ai.parse_menu_items("ผัดไทย 60, ข้าวมันไก่ 55")
    assert len(items) == 2
    assert items[0] == {"thai": "ผัดไทย", "english": "Pad Thai", "price": 60}
    assert items[1]["price"] == 55


def test_parse_menu_items_handles_fenced_response(asks):
    _, set_replies = asks
    set_replies('```\n[{"thai": "X", "english": "Y", "price": 0}]\n```')

    items = ai.parse_menu_items("anything")
    assert items == [{"thai": "X", "english": "Y", "price": 0}]


def test_generate_profile_for_language_uses_lang_config(asks):
    captured, set_replies = asks
    set_replies("日本語のプロフィール")

    class FakeVendor:
        vendor_name_en = "Auntie Noi"
        location_display = "Silom"
        thai_hours = "17:00–23:00"
        thai_payment = "Cash"

    lang_config = {"code": "ja", "label": "日本語", "gemini_instruction": "Write in Japanese"}
    out = ai.generate_profile_for_language(FakeVendor(), lang_config)

    assert out == "日本語のプロフィール"
    prompt = captured[0]
    assert "日本語" in prompt
    assert "Write in Japanese" in prompt
    assert "Auntie Noi" in prompt
    assert "Silom" in prompt


def test_update_living_portrait_weaves_in_note(asks):
    captured, set_replies = asks
    set_replies("Updated profile with new sentence.")

    out = ai.update_living_portrait(
        existing_profile="Existing profile here.",
        new_note="Best pad thai ever",
        visitor_name="Alex",
        checkin_count=42,
    )

    assert out == "Updated profile with new sentence."
    prompt = captured[0]
    assert "Existing profile here." in prompt
    assert "Best pad thai ever" in prompt
    assert "Alex" in prompt
    assert "42" in prompt


def test_ask_calls_correct_model(monkeypatch):
    """_ask must use gemini-2.5-flash-lite per CLAUDE.md."""
    captured = {}

    class FakeResponse:
        text = "  result with whitespace  "

    def fake_generate(*, model, contents):
        captured["model"] = model
        captured["contents"] = contents
        return FakeResponse()

    monkeypatch.setattr(ai._client.models, "generate_content", fake_generate)

    out = ai._ask("hello")
    assert out == "result with whitespace"  # strip() applied
    assert captured["model"] == "gemini-2.5-flash-lite"
    assert captured["contents"] == "hello"
