# soifood tests

Fast, offline test suite. No real Gemini calls (all AI is mocked) and no
Postgres — routes run against an in-memory SQLite engine swapped in for
`main.engine`.

## Layout

```
tests/
  conftest.py   # SQLite engine, TestClient, mocked AI, make_vendor factory
  unit/         # ai.py (mocked _ask), models, sha256 + QR helpers
  routes/       # every FastAPI endpoint via TestClient
  e2e/          # Playwright browser flows against a live uvicorn server
```

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/playwright install chromium   # only needed for e2e
```

## Running

```bash
# Fast suite (unit + routes) — e2e excluded by default
.venv/bin/pytest

# End-to-end browser tests only
.venv/bin/pytest -m e2e

# Everything
.venv/bin/pytest -m "e2e or not e2e"
```

## Notes

- A valid-shaped `.env` must be present (`GEMINI_API_KEY`, `DATABASE_URL`) —
  the app builds its Gemini client and engine at import. Values need not be
  real: the tests mock all AI and use SQLite, so a fake key and an
  unreachable DB URL still pass.
- `@pytest.mark.no_ai_mock` opts a test out of the autouse AI stub (used to
  test the real `ai._ask` → Gemini client wiring with the client mocked).
- e2e tests launch `tests/e2e/_server.py`, a uvicorn entrypoint that points
  the app at on-disk SQLite and stubs every AI function.
