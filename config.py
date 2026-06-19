"""환경 변수 로딩 및 앱 설정."""
import os

from dotenv import load_dotenv

load_dotenv()


def _split(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


# 공통
WEEK_START = os.getenv("WEEK_START", "sunday").strip().lower()
TIMEZONE = os.getenv("TIMEZONE", "Asia/Seoul").strip()
PORT = int(os.getenv("PORT", "5000"))

# Google Calendar
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
GOOGLE_CALENDAR_IDS = _split(os.getenv("GOOGLE_CALENDAR_IDS", ""))

# Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "").strip()
NOTION_DATABASE_IDS = _split(os.getenv("NOTION_DATABASE_IDS", ""))
NOTION_DATE_PROPERTY = os.getenv("NOTION_DATE_PROPERTY", "").strip()
