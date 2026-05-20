import json
import re

import google.generativeai as genai

from config import settings

genai.configure(api_key=settings.gemini_api_key)
_model = genai.GenerativeModel("gemini-2.5-flash-lite")


def _ask(prompt: str) -> str:
    return _model.generate_content(prompt).text.strip()


def generate_thai_summary(vendor_data: dict) -> str:
    prompt = f"""เขียนโปรไฟล์ร้านอาหารริมถนนแบบอบอุ่น 3-4 ประโยค เป็นภาษาไทย
โดยใช้ข้อมูลต่อไปนี้:
- ชื่อร้าน/เจ้าของ: {vendor_data['q1']}
- เมนูและราคา: {vendor_data['q2']}
- ที่ตั้ง: {vendor_data['q3']}
- วันและเวลาเปิด: {vendor_data['q4']}
- การชำระเงิน: {vendor_data['q5']}
- เรื่องราว: {vendor_data['q6']}
ให้รู้สึกถึงความรัก ความอบอุ่น และความภาคภูมิใจ ห้ามใช้หัวข้อหรือ bullet points"""
    return _ask(prompt)


def generate_english_profile(vendor_data: dict, thai_summary: str) -> str:
    prompt = f"""Write a 4-5 sentence English profile for a Bangkok street food vendor.
Tone: like a trusted friend recommending a hidden gem to a newcomer.
Must include: what to order + price, exact location + landmark, days + hours, payment methods, one human detail from their story.

Vendor answers (Thai):
- Name/owner: {vendor_data['q1']}
- Food + prices: {vendor_data['q2']}
- Location: {vendor_data['q3']}
- Hours: {vendor_data['q4']}
- Payment: {vendor_data['q5']}
- Story: {vendor_data['q6']}

Thai summary for reference: {thai_summary}

Write in English only. No bullet points, no headers. Max 5 sentences."""
    return _ask(prompt)


def extract_vendor_names(q1: str, q3: str) -> dict:
    prompt = f"""Extract the English stall name and English location from these Thai vendor answers.
Return ONLY valid JSON, no markdown, no explanation.

Q1 (stall name + owner): {q1}
Q3 (location + landmark): {q3}

Return exactly: {{"vendor_name_en": "...", "location_display": "..."}}
- vendor_name_en: natural English stall name (e.g. "Auntie Noi's Pad Thai")
- location_display: English location with landmark (e.g. "Silom Night Market, near BTS Sala Daeng exit 2")"""
    raw = _ask(prompt)
    # Strip markdown code fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
    return json.loads(raw)


def parse_menu_items(thai_food_price: str) -> list:
    prompt = f"""Parse this Thai street food menu text into a JSON array.
Return ONLY valid JSON, no markdown, no explanation.

Input: {thai_food_price}

Return exactly: [{{"thai": "...", "english": "...", "price": 0}}]
- thai: Thai name as written
- english: natural English translation
- price: integer baht price (0 if not specified)"""
    raw = _ask(prompt)
    raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
    return json.loads(raw)


def generate_profile_for_language(vendor, lang_config: dict) -> str:
    prompt = f"""Translate and adapt this Bangkok street food vendor profile into {lang_config['label']}.
{lang_config['gemini_instruction']}.
Keep the warm, personal tone. Same length as the source. No bullet points, no headers.

English source profile:
{vendor.vendor_name_en} is located at {vendor.location_display}.
Hours: {vendor.thai_hours}. Payment: {vendor.thai_payment}.

Write only in {lang_config['label']}."""
    return _ask(prompt)


def update_living_portrait(existing_profile: str, new_note: str, visitor_name: str, checkin_count: int) -> str:
    prompt = f"""You are updating a Bangkok street food vendor's community profile.
Add exactly one warm new sentence that weaves in this visitor's note.
Keep the total profile to 6 sentences maximum.
Do not use bullet points or headers.

Current profile:
{existing_profile}

New community note from {visitor_name}: "{new_note}"
Total check-ins so far: {checkin_count}

Return the complete updated profile text only."""
    return _ask(prompt)
