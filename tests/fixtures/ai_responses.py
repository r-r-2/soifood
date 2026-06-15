"""Canned Gemini outputs — deterministic stand-ins for ai.py functions."""

THAI_SUMMARY = (
    "ป้าน้อยทำผัดไทยสูตรแม่มากว่า 22 ปี ที่ตลาดนัดสีลม "
    "ผัดไทยกุ้งสด 60 บาท ผัดไทยไก่ 50 บาท เปิดทุกวัน 17:00–23:00 "
    "รับเงินสดและ PromptPay"
)

ENGLISH_PROFILE = (
    "Auntie Noi has been cooking her late mother's pad thai recipe since she was 18 — "
    "now serving Silom Night Market for over 22 years. Fresh prawn pad thai is 60 baht, "
    "chicken 50. Find her near BTS Sala Daeng exit 2, open daily 5pm to 11pm. "
    "Cash or PromptPay accepted."
)

VENDOR_NAMES = {
    "vendor_name_en": "Auntie Noi's Pad Thai",
    "location_display": "Silom Night Market, near BTS Sala Daeng exit 2",
}

MENU_ITEMS = [
    {"thai": "ผัดไทยกุ้งสด", "english": "Fresh prawn pad thai", "price": 60},
    {"thai": "ผัดไทยไก่", "english": "Chicken pad thai", "price": 50},
]

JA_PROFILE = "ノイおばさんはシーロムナイトマーケットで20年以上パッタイを作り続けています。"

UPDATED_PORTRAIT = ENGLISH_PROFILE + " Recent visitor Alex called the prawn pad thai unforgettable."
