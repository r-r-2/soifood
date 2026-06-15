# soifood

"The best meal of your trip is out there. Now you can find it, order it, and never forget the person who made it."

[Project Summary PDF](soifood-presentation.pdf)

[Project Deck](soifood-SEABWBangkokHackathon2026.pdf)

AI-powered street food discovery platform for Bangkok. Gives street food vendors an English digital presence — bilingual menu, community check-ins, and a printable QR card — connecting them with expat and tourist customers.

Built for the [SEABW Bangkok Hackathon 2026](https://www.seablockchainweek.org/hackathon).

---

### Main Pages

- Vendor Onboarding  
  https://soifood.onrender.com/

- Browse Vendors  
  https://soifood.onrender.com/vendors

- Community Leaderboard  
  https://soifood.onrender.com/leaderboard

### Example Vendor Pages

https://soifood.onrender.com/vendor/1
https://soifood.onrender.com/vendor/4

---

## ✨ Features

- 🇹🇭 **Bilingual AI menus**  
  Convert free-text Thai menus into structured Thai + English menus with pricing.

- 🤖 **AI-generated vendor profiles**  
  Gemini creates warm, human-readable English vendor stories during onboarding.

- 📍 **Vendor microsites**  
  Each vendor gets a shareable `/vendor/{id}` page with menu, story, ordering UI, and QR access.

- ❤️ **Community check-ins**  
  Visitors can leave notes and support vendors through lightweight social engagement.

- 🪄 **Living portrait system**  
  Community notes continuously reshape the vendor profile into a living narrative.

- 📱 **Printable QR cards**  
  Vendors receive screenshot-friendly QR cards linking directly to their microsite.

- 🔊 **Thai TTS order playback**  
  Tourist orders can be spoken aloud in Thai using generated audio.

- 🔒 **Privacy-first phone handling**  
  All phone numbers are SHA256-hashed before storage. Raw phone numbers are never stored.

---


## 🧭 Demo Flow

1. Vendor completes a 6-question onboarding flow
2. Gemini generates:
   - English vendor profile
   - bilingual menu structure
3. Vendor microsite becomes instantly available
4. Tourists discover vendors and check in
5. Community activity updates the vendor’s “living portrait”
6. Vendor prints QR card for physical stall display

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn |
| ORM | SQLModel |
| Database | Supabase PostgreSQL |
| AI | Gemini 2.5 Flash-Lite |
| Templates | Jinja2 + Tailwind CDN |
| TTS | gTTS |
| QR Codes | qrcode[pil] |
| Deployment | Render + Docker |

---

## 🧠 Architecture Highlights

### Cache-aside AI profiles
Vendor profiles are generated once during onboarding and cached in the database.  
`GET /vendor/{id}/profile` only calls Gemini on cache miss.

### No-build frontend
Entire frontend uses:
- Jinja2 templates
- Tailwind CDN
- vanilla JavaScript

No npm, bundlers, or frontend build pipeline.

### Client-side ordering
Cart state and ordering flow run entirely in the browser with zero server-side order state.

### Privacy-first design
- Vendor phones hashed server-side
- Visitor phones hashed client-side
- Raw numbers never stored or logged

---

## 📂 Project Structure

```bash
soifood/
├── main.py
├── models.py
├── ai.py
├── config.py
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── Dockerfile
├── Procfile
├── static/
├── templates/
└── tests/
    ├── conftest.py            # env, in-memory SQLite, AI/TTS mocks
    ├── unit/                  # ai.py, models.py, helpers
    ├── routes/                # every FastAPI endpoint
    ├── e2e/                   # Playwright mobile-viewport flows
    └── fixtures/              # canned vendor data + AI responses + live smoke
```

---

## 🧪 Testing

The suite ships with **59 tests** at **100% line coverage** of `ai.py`, `main.py`, `models.py`, and `config.py`. Three layers, all runnable from one command.

### Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium   # only needed for E2E
```

The default `mock_ai` / `mock_gtts` autouse fixtures stub Gemini and gTTS, so **no API key is required** to run tests. The root `conftest.py` sets safe placeholder env vars before any project module imports.

### Run

```bash
# Everything (unit + routes + E2E)         — ~10s
.venv/bin/python -m pytest

# Fast feedback (unit + routes only)       — ~1s
.venv/bin/python -m pytest tests/unit tests/routes

# Browser E2E only                          — ~10s
.venv/bin/python -m pytest tests/e2e

# Coverage report
.venv/bin/python -m pytest --cov=ai --cov=main --cov=models --cov=config --cov-report=term-missing

# Live smoke against real Gemini (opt-in)  — costs $, needs real GEMINI_API_KEY
.venv/bin/python -m pytest -m live tests/fixtures/live_smoke.py
```

### What's covered

| Layer | Files | What it tests |
|---|---|---|
| **Unit** | `tests/unit/` | `ai.py` prompt shape + JSON parsing + markdown-fence stripping; `models.py` defaults + SHA256 phone hash + menu JSON roundtrip; QR PNG generation |
| **Routes** | `tests/routes/` | Every endpoint: onboarding happy + 422, cache-aside hit/miss/bad-lang/404, microsite + card render + 404, QR PNG content-type, check-in (new/repeat/note/no-note/empty-note/persistence/404), leaderboard aggregation + top-20 cap, order audio MP3 + 503 + Thai lang, browse HTML + JSON + inactive filter, seed idempotency |
| **E2E** | `tests/e2e/` | Playwright on iPhone 14 viewport against a real uvicorn subprocess: full onboarding flow + mismatched-phone validation, ordering cart → order card, check-in modal submission, browse-page client-side search |
| **Live smoke** | `tests/fixtures/live_smoke.py` | Opt-in suite hitting the real Gemini API for all 6 `ai.py` functions. Skipped by default. |

### Design notes

- **In-memory SQLite** via `StaticPool` — no Postgres dependency for the test runner. Production Postgres-specific behavior (JSONB, FTS) isn't used, so SQLite is a safe stand-in.
- **AI/TTS mocked by default**, real calls gated behind `@pytest.mark.live`. The `mock_ai` autouse fixture is opt-out per test, so unit tests can exercise the real `ai.py` against a stubbed `_ask`.
- **E2E isolation** — each test module gets a fresh uvicorn subprocess pointed at a tempfile SQLite, with AI stubs injected via `tests/e2e/_app_for_e2e.py` before `main` is imported.

---

## 🌐 API Routes

```http
GET  /                        # onboarding form
GET  /vendors                 # browse vendors
POST /onboard                 # vendor onboarding + AI generation
GET  /vendor/{id}             # vendor microsite
GET  /vendor/{id}/profile     # cached AI profile
GET  /vendor/{id}/card        # printable QR card
GET  /qr/{id}                 # QR PNG
POST /checkin/{id}            # community check-in
GET  /leaderboard             # supporters leaderboard
GET  /order-audio             # Thai TTS audio
GET  /api/vendors             # vendor JSON API
```

---

## 🎨 Design System

Inspired by **Benjarong porcelain aesthetics**:
- Navy blue: `#1a2f4a`
- Antique gold: `#B8924A`
- Thai pattern accents
- DM Sans typography
- Mobile-first layouts

---

## ⚙️ Environment Variables

Create a `.env` file:

```env
DATABASE_URL=
GEMINI_API_KEY=
SECRET_KEY=
```

---

## 🔮 Future Ideas

- Nearby vendor discovery
- “Open now” filtering
- AI food recommendations
- Vendor analytics dashboard
- Multi-language tourist support
- Offline-first QR experience

---