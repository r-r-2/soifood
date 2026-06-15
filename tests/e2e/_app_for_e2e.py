"""Standalone entrypoint for E2E — boots the real app with AI + TTS stubbed.

Launched as a subprocess by tests/e2e/conftest.py. The wrapper:
  - sets env (DATABASE_URL pointed at a tempfile, GEMINI_API_KEY dummy)
  - stubs google.genai so `ai.py` import doesn't reach the network
  - replaces every ai.* function with canned returns
  - replaces gTTS so /order-audio doesn't hit Google Translate
Then runs uvicorn on the port given via the SOIFOOD_E2E_PORT env var.
"""

import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock


def _bootstrap():
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))

    # Stub genai before ai.py imports it.
    fake_genai = types.ModuleType("google.genai")
    fake_genai.Client = MagicMock(return_value=MagicMock())
    fake_google = types.ModuleType("google")
    fake_google.genai = fake_genai
    sys.modules.setdefault("google", fake_google)
    sys.modules["google.genai"] = fake_genai

    import ai

    THAI_SUMMARY = "สรุปไทยสำหรับ E2E"
    ENGLISH_PROFILE = (
        "E2E English profile — Auntie Noi serves Silom Night Market with fresh "
        "prawn pad thai at 60 baht and chicken pad thai at 50."
    )
    VENDOR_NAMES = {
        "vendor_name_en": "E2E Test Stall",
        "location_display": "E2E Location, near BTS Test",
    }
    MENU_ITEMS = [
        {"thai": "ผัดไทยกุ้งสด", "english": "Fresh prawn pad thai", "price": 60},
        {"thai": "ผัดไทยไก่", "english": "Chicken pad thai", "price": 50},
    ]

    ai.generate_thai_summary = lambda data: THAI_SUMMARY
    ai.generate_english_profile = lambda data, thai: ENGLISH_PROFILE
    ai.extract_vendor_names = lambda q1, q3: dict(VENDOR_NAMES)
    ai.parse_menu_items = lambda text: list(MENU_ITEMS)
    ai.generate_profile_for_language = lambda v, cfg: "E2E translated profile"
    ai.update_living_portrait = (
        lambda existing, note, name, count: existing + f" {name} stopped by."
    )

    import main

    main.generate_thai_summary = ai.generate_thai_summary
    main.generate_english_profile = ai.generate_english_profile
    main.extract_vendor_names = ai.extract_vendor_names
    main.parse_menu_items = ai.parse_menu_items
    main.generate_profile_for_language = ai.generate_profile_for_language
    main.update_living_portrait = ai.update_living_portrait

    class _FakeTTS:
        def __init__(self, text, lang, slow=False):
            self.text = text

        def write_to_fp(self, fp):
            fp.write(b"ID3\x03\x00\x00\x00\x00\x00\x00e2e-fake-mp3")

    main.gTTS = _FakeTTS

    return main


if __name__ == "__main__":
    main_module = _bootstrap()
    import uvicorn

    port = int(os.environ["SOIFOOD_E2E_PORT"])
    uvicorn.run(main_module.app, host="127.0.0.1", port=port, log_level="warning")
