from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class Vendor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_name_thai: str
    vendor_name_en: str
    owner_name: str

    # Raw Thai answers from onboarding
    thai_food_price: str        # Q2 — what + price
    thai_location: str          # Q3 — location + landmark
    thai_hours: str             # Q4 — days + hours
    thai_payment: str           # Q5 — payment methods
    thai_story: str             # Q6 — emotional story

    # Gemini-extracted display fields
    location_thai: str
    location_display: str       # English location extracted by Gemini

    # Menu as JSON string — parsed from Q2 by Gemini
    menu_items: str = Field(default="[]")

    # Security — raw phone never stored
    phone_hash: str

    # Optional photo — Supabase Storage public URL
    photo_url: Optional[str] = Field(default=None)

    # Community stats
    checkin_count: int = Field(default=0)
    unique_visitors: int = Field(default=0)
    repeat_visitors: int = Field(default=0)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)


class VendorProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="vendor.id")
    language_code: str          # e.g. "en", "th", "ja", "zh", "ko"
    profile_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CheckIn(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="vendor.id")
    visitor_hash: str           # SHA256 of visitor phone — never store raw
    visitor_name: str
    device_language: Optional[str] = Field(default=None)
    note: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
