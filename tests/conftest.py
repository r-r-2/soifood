"""Root conftest — env setup, in-memory SQLite engine, AI/TTS mocks, TestClient.

Order matters: environment variables and the genai.Client stub must be in place
BEFORE any project module is imported, because:
  - config.Settings() instantiates at import and requires GEMINI_API_KEY/DATABASE_URL
  - ai.py builds genai.Client(api_key=...) at import time

Both are handled at the top of this file so any later `from main import app`
inside a fixture or test sees a fully wired test environment.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# 1. Env first — must be set before `config` is ever imported.
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("BASE_URL", "http://testserver")

# 2. Make project root importable (tests/ is a sibling of main.py).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 3. Stub google.genai so `ai.py` import doesn't try to talk to Google.
import types  # noqa: E402

_fake_genai = types.ModuleType("google.genai")
_fake_genai.Client = MagicMock(return_value=MagicMock())
_fake_google = types.ModuleType("google")
_fake_google.genai = _fake_genai
sys.modules.setdefault("google", _fake_google)
sys.modules["google.genai"] = _fake_genai

# 4. Now safe to import third-party + project modules.
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from tests.fixtures import ai_responses  # noqa: E402


# ── Engine / DB ───────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    """Fresh in-memory SQLite per test, shared across the test's connection pool."""
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


# ── AI / TTS mocks (autouse — every test gets deterministic AI by default) ────

@pytest.fixture(autouse=True)
def mock_ai(request, monkeypatch):
    """Patch every ai.py function with a canned return.

    Tests marked @pytest.mark.live opt out and hit the real Gemini API.
    """
    if request.node.get_closest_marker("live"):
        return

    import ai

    monkeypatch.setattr(ai, "generate_thai_summary", lambda data: ai_responses.THAI_SUMMARY)
    monkeypatch.setattr(
        ai, "generate_english_profile",
        lambda data, thai: ai_responses.ENGLISH_PROFILE,
    )
    monkeypatch.setattr(ai, "extract_vendor_names", lambda q1, q3: dict(ai_responses.VENDOR_NAMES))
    monkeypatch.setattr(ai, "parse_menu_items", lambda text: list(ai_responses.MENU_ITEMS))
    monkeypatch.setattr(
        ai, "generate_profile_for_language",
        lambda vendor, lang_config: ai_responses.JA_PROFILE,
    )
    monkeypatch.setattr(
        ai, "update_living_portrait",
        lambda existing, note, name, count: ai_responses.UPDATED_PORTRAIT,
    )

    # Also patch the references that main.py imported at module load.
    import main
    monkeypatch.setattr(main, "generate_thai_summary", ai.generate_thai_summary)
    monkeypatch.setattr(main, "generate_english_profile", ai.generate_english_profile)
    monkeypatch.setattr(main, "extract_vendor_names", ai.extract_vendor_names)
    monkeypatch.setattr(main, "parse_menu_items", ai.parse_menu_items)
    monkeypatch.setattr(main, "generate_profile_for_language", ai.generate_profile_for_language)
    monkeypatch.setattr(main, "update_living_portrait", ai.update_living_portrait)


@pytest.fixture(autouse=True)
def mock_gtts(request, monkeypatch):
    """Replace gTTS with a stub that writes a tiny fake MP3 payload."""
    if request.node.get_closest_marker("live"):
        return

    class _FakeTTS:
        def __init__(self, text, lang, slow=False):
            self.text = text
            self.lang = lang

        def write_to_fp(self, fp):
            # ID3 header bytes — enough to look like an mp3 to a casual sniff.
            fp.write(b"ID3\x03\x00\x00\x00\x00\x00\x00fake-mp3-bytes")

    import main
    monkeypatch.setattr(main, "gTTS", _FakeTTS)


# ── App / client fixture ──────────────────────────────────────────────────────

@pytest.fixture
def client(engine, monkeypatch):
    """TestClient with main.engine swapped to the in-memory SQLite engine.

    The lifespan handler (which seeds 3 vendors) runs when TestClient enters
    its context manager.
    """
    import main
    monkeypatch.setattr(main, "engine", engine)

    with TestClient(main.app) as c:
        yield c


@pytest.fixture
def empty_client(engine, monkeypatch):
    """Client backed by an engine where seed_data is suppressed.

    Use when a test needs to assert against an empty DB or insert its own
    fixtures without the 3 seed vendors getting in the way.
    """
    import main
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(main, "seed_data", lambda session: None)

    with TestClient(main.app) as c:
        yield c
