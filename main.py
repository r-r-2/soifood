import hashlib
import io
import json
from contextlib import asynccontextmanager
from typing import Optional

import qrcode
from fastapi import FastAPI, Form, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from gtts import gTTS
from sqlmodel import Session, SQLModel, create_engine, select

from ai import (
    extract_vendor_names,
    generate_english_profile,
    generate_profile_for_language,
    generate_thai_summary,
    parse_menu_items,
    update_living_portrait,
)
from config import SUPPORTED_LANGUAGES, settings
from models import CheckIn, Vendor, VendorProfile

engine = create_engine(settings.database_url)


# ── Seed data ─────────────────────────────────────────────────────────────────

def seed_data(session: Session):
    if session.exec(select(Vendor)).first():
        return

    _seeds = [
        {
            "vendor_name_thai": "ร้านป้าน้อย",
            "vendor_name_en": "Auntie Noi's Pad Thai",
            "owner_name": "ป้าน้อย สมใจ",
            "thai_food_price": "ผัดไทยกุ้งสด 60 บาท, ผัดไทยไก่ 50 บาท",
            "thai_location": "ตลาดนัดสีลม ใกล้ BTS ศาลาแดง ทางออก 2",
            "thai_hours": "ทุกวัน 17:00–23:00",
            "thai_payment": "เงินสด และ PromptPay",
            "thai_story": "ทำผัดไทยมาตั้งแต่อายุ 18 ปี เพื่อส่งน้องเรียน สูตรมาจากแม่ที่สอนไว้ก่อนเสียชีวิต",
            "location_thai": "ตลาดนัดสีลม ใกล้ BTS ศาลาแดง ทางออก 2",
            "location_display": "Silom Night Market, near BTS Sala Daeng exit 2",
            "menu_items": json.dumps([
                {"thai": "ผัดไทยกุ้งสด", "english": "Fresh prawn pad thai", "price": 60},
                {"thai": "ผัดไทยไก่", "english": "Chicken pad thai", "price": 50},
            ]),
            "phone_hash": hashlib.sha256(b"seed-vendor-1").hexdigest(),
            "checkin_count": 87, "unique_visitors": 43, "repeat_visitors": 28,
            "en": "Auntie Noi has been cooking her late mother's pad thai recipe since she was 18 — over 22 years at Silom Night Market. Fresh prawn pad thai is 60 baht, chicken 50. Find her near BTS Sala Daeng exit 2, open daily 5pm to midnight. Cash or PromptPay.",
            "th": "ป้าน้อยทำผัดไทยสูตรแม่มากว่า 22 ปีแล้ว ด้วยความรักและความทุ่มเท",
        },
        {
            "vendor_name_thai": "ร้านลุงสมชาย",
            "vendor_name_en": "Uncle Somchai's Khao Man Gai",
            "owner_name": "สมชาย วงศ์ดี",
            "thai_food_price": "ข้าวมันไก่ 55 บาท, ข้าวหมูแดง 50 บาท",
            "thai_location": "หน้าโรงพยาบาลจุฬา ถนนพระราม 4 ใกล้ BTS ศาลาแดง",
            "thai_hours": "จันทร์–เสาร์ 06:00–14:00",
            "thai_payment": "เงินสดเท่านั้น",
            "thai_story": "ขายข้าวมันไก่มา 15 ปี เลี้ยงลูก 3 คนจนจบมหาวิทยาลัยทั้งหมด ภูมิใจมาก",
            "location_thai": "หน้าโรงพยาบาลจุฬา ถนนพระราม 4 ใกล้ BTS ศาลาแดง",
            "location_display": "Rama 4 Rd, near Chulalongkorn Hospital",
            "menu_items": json.dumps([
                {"thai": "ข้าวมันไก่", "english": "Chicken rice (Khao Man Gai)", "price": 55},
                {"thai": "ข้าวหมูแดง", "english": "Red pork rice", "price": 50},
            ]),
            "phone_hash": hashlib.sha256(b"seed-vendor-2").hexdigest(),
            "checkin_count": 54, "unique_visitors": 31, "repeat_visitors": 18,
            "en": "Uncle Somchai has been feeding the Chulalongkorn Hospital crowd for 15 years — his khao man gai put all three of his children through university. Chicken rice is 55 baht, red pork rice 50. Cash only. Open Monday to Saturday 6am to 2pm — come early, he sells out.",
            "th": "ลุงสมชายต้มไก่สดทุกเช้า น้ำซุปเข้มข้น หอมกลิ่นตั้งแต่เช้าตรู่",
        },
        {
            "vendor_name_thai": "ร้านแม่แดง",
            "vendor_name_en": "Mae Daeng's Isaan Som Tam",
            "owner_name": "แดง ใจดี",
            "thai_food_price": "ส้มตำไทย 50 บาท, ลาบหมู 60 บาท, ข้าวเหนียว 10 บาท",
            "thai_location": "ตลาด อตก. ใกล้ BTS อารีย์ ทางออก 3",
            "thai_hours": "ทุกวัน 11:00–20:00",
            "thai_payment": "เงินสด และ PromptPay",
            "thai_story": "ย้ายจากอุดรธานีมากรุงเทพ 10 ปีที่แล้ว อยากให้คนกรุงได้กินส้มตำแบบอีสานแท้ๆ พริกสั่งตรงจากบ้าน",
            "location_thai": "ตลาด อตก. ใกล้ BTS อารีย์ ทางออก 3",
            "location_display": "Or Tor Kor Market, near BTS Ari exit 3",
            "menu_items": json.dumps([
                {"thai": "ส้มตำไทย", "english": "Thai green papaya salad (Som Tam)", "price": 50},
                {"thai": "ลาบหมู", "english": "Spicy minced pork salad (Larb)", "price": 60},
                {"thai": "ข้าวเหนียว", "english": "Sticky rice", "price": 10},
            ]),
            "phone_hash": hashlib.sha256(b"seed-vendor-3").hexdigest(),
            "checkin_count": 32, "unique_visitors": 22, "repeat_visitors": 8,
            "en": "Mae Daeng left Udon Thani 10 years ago with one mission: to bring real Isaan food to Bangkok. She orders her chilies directly from home — the som tam (50 baht) has authentic heat. Find her at Or Tor Kor Market near BTS Ari exit 3, open daily 11am to 8pm. Cash or PromptPay.",
            "th": "แม่แดงนำความอร่อยแบบอีสานแท้จากอุดรธานีมาสู่กรุงเทพ",
        },
    ]

    for s in _seeds:
        vendor = Vendor(
            vendor_name_thai=s["vendor_name_thai"],
            vendor_name_en=s["vendor_name_en"],
            owner_name=s["owner_name"],
            thai_food_price=s["thai_food_price"],
            thai_location=s["thai_location"],
            thai_hours=s["thai_hours"],
            thai_payment=s["thai_payment"],
            thai_story=s["thai_story"],
            location_thai=s["location_thai"],
            location_display=s["location_display"],
            menu_items=s["menu_items"],
            phone_hash=s["phone_hash"],
            checkin_count=s["checkin_count"],
            unique_visitors=s["unique_visitors"],
            repeat_visitors=s["repeat_visitors"],
        )
        session.add(vendor)
        session.flush()
        session.add(VendorProfile(vendor_id=vendor.id, language_code="en", profile_text=s["en"]))
        session.add(VendorProfile(vendor_id=vendor.id, language_code="th", profile_text=s["th"]))

    session.commit()


# ── App setup ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_data(session)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def onboard_form(request: Request):
    return templates.TemplateResponse("onboard.html", {"request": request})


@app.get("/vendors")
def browse_vendors(request: Request):
    return templates.TemplateResponse("vendors.html", {"request": request})


@app.post("/onboard")
async def onboard_vendor(
    q1: str = Form(...),
    q2: str = Form(...),
    q3: str = Form(...),
    q4: str = Form(...),
    q5: str = Form(...),
    q6: str = Form(...),
    phone_hash: str = Form(...),
):
    vendor_data = {"q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5, "q6": q6}

    names = extract_vendor_names(q1, q3)
    menu = parse_menu_items(q2)
    thai_summary = generate_thai_summary(vendor_data)
    english_profile = generate_english_profile(vendor_data, thai_summary)

    with Session(engine) as session:
        vendor = Vendor(
            vendor_name_thai=q1,
            vendor_name_en=names["vendor_name_en"],
            owner_name=q1,
            thai_food_price=q2,
            thai_location=q3,
            thai_hours=q4,
            thai_payment=q5,
            thai_story=q6,
            location_thai=q3,
            location_display=names["location_display"],
            menu_items=json.dumps(menu),
            phone_hash=phone_hash,
        )
        session.add(vendor)
        session.flush()
        session.add(VendorProfile(vendor_id=vendor.id, language_code="th", profile_text=thai_summary))
        session.add(VendorProfile(vendor_id=vendor.id, language_code="en", profile_text=english_profile))
        session.commit()
        session.refresh(vendor)
        return RedirectResponse(url=f"/vendor/{vendor.id}", status_code=303)


@app.get("/vendor/{vendor_id}")
def vendor_microsite(request: Request, vendor_id: int):
    with Session(engine) as session:
        vendor = session.get(Vendor, vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        profiles = session.exec(
            select(VendorProfile).where(VendorProfile.vendor_id == vendor_id)
        ).all()
        profile_map = {p.language_code: p.profile_text for p in profiles}

        recent_checkins = session.exec(
            select(CheckIn)
            .where(CheckIn.vendor_id == vendor_id)
            .where(CheckIn.note.isnot(None))
            .order_by(CheckIn.created_at.desc())
            .limit(5)
        ).all()

        menu_items = json.loads(vendor.menu_items or "[]")

        return templates.TemplateResponse("vendor.html", {
            "request": request,
            "vendor": vendor,
            "profile_map": profile_map,
            "menu_items": menu_items,
            "recent_checkins": recent_checkins,
            "supported_languages": SUPPORTED_LANGUAGES,
            "base_url": settings.base_url,
        })


@app.get("/vendor/{vendor_id}/profile")
def vendor_profile(vendor_id: int, lang: str = "en"):
    lang_config = next((l for l in SUPPORTED_LANGUAGES if l["code"] == lang), None)
    if not lang_config:
        return JSONResponse({"error": "Unsupported language"}, status_code=400)

    with Session(engine) as session:
        vendor = session.get(Vendor, vendor_id)
        if not vendor:
            return JSONResponse({"error": "Vendor not found"}, status_code=404)

        existing = session.exec(
            select(VendorProfile)
            .where(VendorProfile.vendor_id == vendor_id)
            .where(VendorProfile.language_code == lang)
        ).first()

        if existing:
            return JSONResponse({"profile_text": existing.profile_text})

        # Cache miss — generate and store
        profile_text = generate_profile_for_language(vendor, lang_config)
        session.add(VendorProfile(vendor_id=vendor_id, language_code=lang, profile_text=profile_text))
        session.commit()
        return JSONResponse({"profile_text": profile_text})


@app.get("/vendor/{vendor_id}/card")
def vendor_card(request: Request, vendor_id: int):
    with Session(engine) as session:
        vendor = session.get(Vendor, vendor_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        return templates.TemplateResponse("card.html", {
            "request": request,
            "vendor": vendor,
            "base_url": settings.base_url,
        })


@app.get("/qr/{vendor_id}")
def vendor_qr(vendor_id: int):
    url = f"{settings.base_url}/vendor/{vendor_id}"
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a2f4a", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png", headers={
        "Content-Disposition": f"attachment; filename=soifood-vendor-{vendor_id}.png"
    })


@app.post("/checkin/{vendor_id}")
async def checkin(
    vendor_id: int,
    visitor_hash: str = Form(...),
    visitor_name: str = Form(...),
    note: Optional[str] = Form(default=None),
    device_language: Optional[str] = Form(default=None),
):
    with Session(engine) as session:
        vendor = session.get(Vendor, vendor_id)
        if not vendor:
            return JSONResponse({"error": "Vendor not found"}, status_code=404)

        prior = session.exec(
            select(CheckIn)
            .where(CheckIn.vendor_id == vendor_id)
            .where(CheckIn.visitor_hash == visitor_hash)
        ).first()

        session.add(CheckIn(
            vendor_id=vendor_id,
            visitor_hash=visitor_hash,
            visitor_name=visitor_name,
            note=note or None,
            device_language=device_language,
        ))

        vendor.checkin_count += 1
        if prior:
            vendor.repeat_visitors += 1
        else:
            vendor.unique_visitors += 1
        session.add(vendor)

        if note and note.strip():
            en_profile = session.exec(
                select(VendorProfile)
                .where(VendorProfile.vendor_id == vendor_id)
                .where(VendorProfile.language_code == "en")
            ).first()
            if en_profile:
                en_profile.profile_text = update_living_portrait(
                    en_profile.profile_text, note, visitor_name, vendor.checkin_count
                )
                session.add(en_profile)

        session.commit()
        return JSONResponse({"points": 10, "total_checkins": vendor.checkin_count})


@app.get("/leaderboard")
def leaderboard(request: Request):
    with Session(engine) as session:
        checkins = session.exec(select(CheckIn)).all()

    stats: dict[str, dict] = {}
    for c in checkins:
        if c.visitor_hash not in stats:
            stats[c.visitor_hash] = {"name": c.visitor_name, "total": 0, "vendors": set()}
        stats[c.visitor_hash]["total"] += 1
        stats[c.visitor_hash]["vendors"].add(c.vendor_id)

    board = sorted(
        [{"name": v["name"], "points": v["total"] * 10, "vendors": len(v["vendors"])}
         for v in stats.values()],
        key=lambda x: x["points"],
        reverse=True,
    )[:20]

    return templates.TemplateResponse("leaderboard.html", {"request": request, "board": board})


@app.get("/order-audio")
def order_audio(text: str):
    try:
        tts = gTTS(text=text, lang="th", slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="audio/mpeg")
    except Exception:
        return Response(status_code=503)


@app.get("/api/vendors")
def api_vendors():
    with Session(engine) as session:
        vendors = session.exec(select(Vendor).where(Vendor.is_active == True)).all()

    result = []
    for v in vendors:
        menu = json.loads(v.menu_items or "[]")
        result.append({
            "id": v.id,
            "vendor_name_thai": v.vendor_name_thai,
            "vendor_name_en": v.vendor_name_en,
            "location_display": v.location_display,
            "checkin_count": v.checkin_count,
            "first_item": menu[0]["english"] if menu else "",
            "photo_url": v.photo_url,
        })

    return JSONResponse(result)
