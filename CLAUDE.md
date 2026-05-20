# soifood — Claude Code Instructions

## What this project is
soifood is an AI-powered street food discovery platform for Bangkok.
It gives street food vendors a multilingual digital presence, a bilingual menu,
and community check-ins — connecting them with expat and tourist customers.
Built for SEABW Bangkok hackathon, May 20 2026.

## Icons and manifest
All favicon files already present in static/ — do not regenerate or overwrite them:
- favicon.ico, favicon-16x16.png, favicon-32x32.png
- apple-touch-icon.png, android-chrome-192x192.png, android-chrome-512x512.png
- site.webmanifest — already configured with name: "soifood", theme_color: "#1a2f4a"
- logo.png — soifood logo, use in header and og-banner

Add to every template <head>:
```html
<link rel="icon" type="image/x-icon" href="/static/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/static/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/static/apple-touch-icon.png">
<link rel="manifest" href="/static/site.webmanifest">
<meta name="theme-color" content="#1a2f4a">
```
- Never write "SoiFood", "Soifood", or "SOIFOOD"
- Logo file: static/logo.png — fallback to text "soifood" in --bkk-gold if not available

## Stack
- Backend: FastAPI + SQLModel
- Database: Supabase PostgreSQL via DATABASE_URL
- AI: Gemini 2.5 Flash-Lite — model string `gemini-2.5-flash-lite`
- TTS: gTTS (Thai audio for order summary — lang='th')
- Templates: Jinja2 + Tailwind CSS CDN (no npm, no build step)
- Deployment: Railway (auto-detects Dockerfile)

## Design system
- Style: Benjarong porcelain — dark navy + warm antique gold + lai Thai pattern accents
- Font: DM Sans (Google Fonts) — matches rounded wordmark in logo exactly
  Load: `<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">`
- Colors extracted from soifood logo (exact match):
  --bkk-bg: #1a2f4a       (logo navy background)
  --bkk-card: #1e3a5f     (card surface)
  --bkk-border: #2a4a6e   (border)
  --bkk-gold: #B8924A     (logo gold — warm antique)
  --bkk-gold-light: #D4AA6A (hover/secondary gold)
  --bkk-red: #8B0000      (spicy/danger)
  --bkk-jade: #1a4a1a     (open/success)
  --bkk-white: #FFFFFF    (logo wordmark white)
  --bkk-muted: #4a6a8a    (muted text)
- Lai Thai SVG pattern borders at section tops/bottoms — thin gold lines, same weight as logo bowl pattern
- Mobile-first — all templates optimised for phones
- Logo icon style: thin line weight strokes — match in any SVG icons used

## Critical rules — never break these
- NO hardcoded API keys — always use `settings` from config.py
- NO React, NO npm, NO build step — Jinja2 templates only
- NO SQLite — Supabase PostgreSQL via DATABASE_URL only
- NO raw phone numbers stored anywhere — SHA256 hash only
- NO Typhoon — Gemini handles all AI tasks (Thai + English + multilingual)
- NO VendorScore or bank dashboard — these are Phase 2, not MVP
- Always use model string `gemini-2.5-flash-lite` — never other models
- Always mobile-first templates

## Secrets management
All secrets via pydantic-settings Settings class in config.py:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gemini_api_key: str
    database_url: str
    base_url: str = "http://localhost:8000"
    supabase_project_url: str = ""
    supabase_anon_public_key: str = ""

    class Config:
        env_file = ".env"
```
Import `settings` everywhere — never use os.getenv() directly.

## Key architecture decisions
- VendorProfile table stores ALL language profiles (not hardcoded fields)
- SUPPORTED_LANGUAGES in config.py — add one dict to support a new language
- Profiles generated lazily on first visitor request (cache-aside pattern)
- GET /vendor/{id}/profile?lang=XX — checks DB first, generates if missing
- Ordering system is 100% frontend JavaScript — no server calls
- Order card is a full-screen div overlay — not a new page
- Cart resets on page refresh — intentional
- Phone numbers: vendor double-entry confirmation, visitor single entry
- Both hashed SHA256 client-side before sending to server

## Database models
- Vendor — core vendor data + menu_items JSON + photo_url (optional)
- VendorProfile — language_code + profile_text (lazy generated)
- CheckIn — visitor_hash + visitor_name + note

## AI functions (all in ai.py using Gemini)
- generate_thai_summary(vendor_data) — warm Thai profile
- generate_english_profile(vendor_data, thai_summary) — expat-friendly English
- extract_vendor_names(q1, q3) — extracts vendor_name_en + location_display
- parse_menu_items(thai_food_price) — returns JSON array of menu items
- generate_profile_for_language(vendor, lang_config) — lazy multilingual
- update_living_portrait(profile, note, name, count) — adds community note

## Vendor onboarding — 6 required questions (Thai)
Q1: ชื่อร้านและชื่อของคุณคืออะไร?
Q2: คุณขายอะไร และราคาเท่าไหร่?
Q3: ร้านของคุณอยู่ที่ไหน? ใกล้อะไรบ้าง?
Q4: เปิดวันไหนบ้าง และกี่โมงถึงกี่โมง?
Q5: รับชำระเงินด้วยวิธีไหนบ้าง?
Q6: ทำไมคุณถึงทำอาหารนี้? มีเรื่องราวอะไรเบื้องหลังบ้าง?
+ Phone number (enter + confirm, double-entry validation)

## Routes
GET  /                          — vendor onboarding form
GET  /vendors                   — browse all vendors + location search
POST /onboard                   — submit vendor + run all AI functions
GET  /vendor/{id}               — vendor microsite
GET  /vendor/{id}/profile       — lazy language profile (cache-aside)
GET  /vendor/{id}/card          — printable QR card
GET  /qr/{id}                   — QR code PNG download
POST /checkin/{id}              — log check-in + return points
GET  /leaderboard               — community leaderboard
GET  /order-audio               — Thai TTS via gTTS → MP3
GET  /api/vendors               — JSON vendor list for browse page search

## Templates
- onboard.html  — vendor onboarding (Thai, mobile-first)
- vendors.html  — browse + location search (client-side JS filtering)
- vendor.html   — microsite (bilingual, menu, ordering, check-in, share, QR)
- card.html     — printable QR card (minimal, screenshot-friendly)
- leaderboard.html — community supporters

## Order card (vendor-facing)
- Thai item name: 32px bold
- English item name: 14px
- Quantity: 28px gold
- Total: 48px bold gold
- 🔊 Audio button: calls /order-audio, plays MP3, 48x48px tap target
- On audio fail: show English message "Audio unavailable — please show this screen to the vendor"

## Commit style
feat: description of feature
fix: description of bug fix
Build one feature at a time — confirm working before next commit.
Never commit broken code.

## Build order
1. Config files (Dockerfile, docker-compose, requirements, .env.example, .gitignore, Procfile, config.py)
2. models.py
3. ai.py
4. main.py + all routes + seed data
5. onboard.html
6. vendors.html
7. vendor.html (profile + menu + ordering + check-in + share)
8. card.html
9. leaderboard.html
10. Deploy to Railway
11. Photo upload via Supabase Storage (last — optional)

## Phase 2 (do NOT build these in MVP)
- VendorScore credit scoring
- Bank / MFI dashboard
- Vendor voice notes
- Weekly vendor spotlight blog
- Expand to Ho Chi Minh City, Jakarta, Yangon