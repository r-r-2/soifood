"""Unit tests for the _strip_html_chars defense-in-depth sanitizer."""

import pytest

from main import _strip_html_chars


@pytest.mark.parametrize("payload,expected", [
    ("<script>alert(1)</script>", "scriptalert(1)/script"),
    ("<img src=x onerror=alert(1)>", "img src=x onerror=alert(1)"),
    ('" onclick="alert(1)', " onclick=alert(1)"),
    ("`backticks`", "backticks"),
    ("Auntie Noi's Pad Thai", "Auntie Noi's Pad Thai"),  # apostrophe preserved
    ("ผัดไทยกุ้งสด 60 บาท", "ผัดไทยกุ้งสด 60 บาท"),         # Thai untouched
    ("", ""),
    ("normal text", "normal text"),
])
def test_strip_removes_dangerous_chars_only(payload, expected):
    assert _strip_html_chars(payload) == expected


def test_strip_handles_none_safely():
    assert _strip_html_chars(None) == ""


def test_strip_removes_combined_attack():
    payload = '<img src="x" onerror=`fetch(\'//evil\')`>'
    out = _strip_html_chars(payload)
    assert "<" not in out
    assert ">" not in out
    assert '"' not in out
    assert "`" not in out
    # Apostrophe stays
    assert "'" in out
