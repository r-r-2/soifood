# soifood

"The best meal of your trip is out there. Now you can find it, order it, and never forget the person who made it."

[Project Overview PDF](.soifood-presentation.pdf)

AI-powered street food discovery platform for Bangkok. Gives street food vendors an English digital presence — bilingual menu, community check-ins, and a printable QR card — connecting them with expat and tourist customers.

Built for the [SEABW Bangkok Hackathon 2026](https://www.seablockchainweek.org/hackathon).

---

### Main Pages

- [Vendor Onboarding](https://soifood.onrender.com/)
- [Browse Vendors](https://soifood.onrender.com/vendors)
- [Community Leaderboard](https://soifood.onrender.com/leaderboard)

### Example Vendor Pages

Replace `{id}` with a real vendor ID.

- `https://soifood.onrender.com/vendor/{id}`
- `https://soifood.onrender.com/vendor/{id}/card`
- `https://soifood.onrender.com/vendor/{id}/profile`

---

## What it does

- **Vendor onboarding** — 6-question form captures name, menu, location, hours, payment, and the vendor's story
- **AI profile generation** — Gemini produces a warm English profile at onboard time
- **Vendor microsite** — each vendor gets a `/vendor/{id}` page with their story, menu, and check-in
- **Bilingual menu** — Thai item names + English translation + price, parsed from free-text input by Gemini
- **Client-side ordering** — cart built entirely in frontend JS, no server calls; order card overlay with Thai TTS audio
- **Community check-ins** — visitors leave their name + note; top supporters shown on leaderboard
- **Living portrait** — each check-in note is woven into the vendor's profile by Gemini (rolling 6-sentence max)
- **Printable QR card** — `/vendor/{id}/card` generates a screenshot-friendly card with QR code

---

## Tech stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI + Uvicorn |
| **ORM / models** | SQLModel (Pydantic v2 + SQLAlchemy core) |
| **Database** | Supabase PostgreSQL |
| **AI** | Google Gemini 2.5 Flash-Lite via `google-genai` SDK |
| **TTS** | gTTS — Thai audio for order summary |
| **Templates** | Jinja2 + Tailwind CSS CDN (no npm, no build step) |
| **QR codes** | `qrcode[pil]` — PNG served inline at `/qr/{id}` |
| **Config** | pydantic-settings — all secrets via environment variables |
| **Container** | Docker (python:3.11-slim) |
| **Deployment** | Render (auto-detects Dockerfile, injects `$PORT`) |

---

## Architecture decisions

**Cache-aside for profiles** — English profile is generated at onboard time. `GET /vendor/{id}/profile` checks DB first, calls Gemini only on miss.

**Phone privacy** — vendor phone is SHA256-hashed server-side before storage. Visitor phone is SHA256-hashed client-side before sending. Raw phone numbers are never stored or logged anywhere.

**No-build frontend** — all interactivity is vanilla JS in Jinja2 templates. Order cart state lives in a JS array; the order card is a full-screen `div` overlay, not a new page. Cart resets on page refresh by design.

---

## Project structure

```
soifood/
├── main.py          # All FastAPI routes (11 endpoints)
├── models.py        # Vendor, VendorProfile, CheckIn — SQLModel tables
├── ai.py            # All Gemini calls (profiles, menu parsing, living portrait)
├── config.py        # pydantic-settings + language config
├── requirements.txt
├── Dockerfile
├── Procfile
├── static/          # favicon set, logo.png, site.webmanifest
└── templates/
    ├── onboard.html     # Vendor onboarding — mobile-first
    ├── vendors.html     # Browse + client-side location search
    ├── vendor.html      # Vendor microsite — menu, ordering, check-in, QR
    ├── card.html        # Printable QR card
    └── leaderboard.html # Community supporters
```

---

## Database models

**`Vendor`** — core vendor record. Stores onboarding answers, Gemini-extracted `vendor_name_en` and `location_display`, menu as a JSON string, `phone_hash`, community counters, and optional `photo_url`.

**`VendorProfile`** — one row per `(vendor_id, language_code)`. Holds the AI-generated profile text.

**`CheckIn`** — one row per visitor check-in. Stores `visitor_hash` (SHA256), visitor name, and optional note.

---

## API routes

```
GET  /                        — vendor onboarding form
GET  /vendors                 — browse all vendors
POST /onboard                 — submit vendor; runs all AI generation
GET  /vendor/{id}             — vendor microsite
GET  /vendor/{id}/profile     — AI profile (cache-aside)
GET  /vendor/{id}/card        — printable QR card
GET  /qr/{id}                 — QR code PNG
POST /checkin/{id}            — log check-in, return updated count
GET  /leaderboard             — community supporters
GET  /order-audio             — Thai TTS audio
GET  /api/vendors             — JSON list for client-side search
```

---

## Design system

Aesthetic: Benjarong porcelain — dark navy (`#1a2f4a`) + warm antique gold (`#B8924A`) + lai Thai pattern accents. Font: DM Sans. Mobile-first throughout.
# soifood

AI-powered street food discovery platform for Bangkok.  
soifood gives Bangkok street food vendors an instant English digital presence through AI-generated profiles, bilingual menus, community check-ins, and printable QR cards — helping tourists and expats discover authentic local food.

Built for the **SEABW Bangkok Hackathon 2026**.

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

## 🎥 Demo

- Live App: https://your-app-url.com
- Demo Video: https://youtube.com/your-demo
- Devpost / Hackathon Submission: https://devpost.com/software/soifood

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
├── Dockerfile
├── Procfile
├── static/
└── templates/
```

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

## 🚀 Local Development

### Clone repository

```bash
git clone https://github.com/yourusername/soifood.git
cd soifood
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run locally

```bash
uvicorn main:app --reload
```

App runs at:

```txt
http://127.0.0.1:8000
```

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

## 🤝 Contributing

Pull requests and ideas are welcome.

---

## 📄 License

MIT