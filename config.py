from pydantic_settings import BaseSettings

SUPPORTED_LANGUAGES = [
    {"code": "en", "label": "English", "gemini_instruction": "Write in English", "generate_on_onboard": True},
    {"code": "th", "label": "ภาษาไทย", "gemini_instruction": "Write in Thai", "generate_on_onboard": True},
    {"code": "ja", "label": "日本語", "gemini_instruction": "Write in Japanese", "generate_on_onboard": False},
    {"code": "zh", "label": "中文", "gemini_instruction": "Write in Simplified Chinese", "generate_on_onboard": False},
    {"code": "ko", "label": "한국어", "gemini_instruction": "Write in Korean", "generate_on_onboard": False},
]


class Settings(BaseSettings):
    gemini_api_key: str
    database_url: str
    base_url: str = "http://localhost:8000"
    supabase_project_url: str = ""
    supabase_anon_public_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
