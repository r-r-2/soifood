"""Standalone launcher for e2e tests.

Runs the real FastAPI app but against an on-disk SQLite database with every
Gemini call stubbed, so browser tests are deterministic and offline.

Usage:  python tests/e2e/_server.py <db_path> <port>
"""
import sys
from unittest.mock import patch

import uvicorn
from sqlmodel import SQLModel, create_engine


def main(db_path: str, port: int):
    # Build a SQLite engine and point the app at it BEFORE importing routes
    # that capture `engine` at call time (they read the module global).
    engine = create_engine(f"sqlite:///{db_path}",
                           connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    import main
    main.engine = engine

    # Stub all AI so onboarding/profile generation never hits the network.
    stubs = [
        patch("main.extract_vendor_names",
              return_value={"vendor_name_en": "E2E Test Stall",
                            "location_display": "E2E Market, near BTS Test"}),
        patch("main.parse_menu_items",
              return_value=[{"thai": "ผัดไทย", "english": "Pad Thai", "price": 60}]),
        patch("main.generate_thai_summary", return_value="สรุปภาษาไทยสำหรับทดสอบ"),
        patch("main.generate_english_profile",
              return_value="A warm English profile for testing."),
        patch("main.generate_profile_for_language", return_value="Generated profile."),
        patch("ai._ask", return_value="stub"),
    ]
    for s in stubs:
        s.start()

    uvicorn.run(main.app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
