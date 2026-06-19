"""환경 변수 로딩 및 앱 설정."""
import json
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

# credentials.json에서 client_id 추출 (관리자 로그인 토큰 검증용)
try:
    with open(GOOGLE_CREDENTIALS_FILE, encoding="utf-8") as _f:
        _data = json.load(_f)
        GOOGLE_CLIENT_ID = (_data.get("installed") or _data.get("web") or {}).get("client_id", "")
except Exception:
    GOOGLE_CLIENT_ID = ""

# 관리자 모드: Google 로그인 이메일이 이 목록에 있으면 관리자
ADMIN_EMAILS = _split(os.getenv("ADMIN_EMAILS", ""))
SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-change-me")

# 공개 카테고리
CATEGORIES = ["private", "busy", "public"]
CATEGORY_LABELS = {"private": "비공개", "busy": "타인 일정", "public": "공개"}
CATEGORY_EMOJI = {"private": "🔒", "busy": "👤", "public": "🌐"}
# 아직 분류 안 한 Notion 일정의 기본값 (안전하게 비공개)
DEFAULT_NOTION_CATEGORY = os.getenv("DEFAULT_NOTION_CATEGORY", "private").strip()
if DEFAULT_NOTION_CATEGORY not in CATEGORIES:
    DEFAULT_NOTION_CATEGORY = "private"
# 외부에 마스킹되어 표시될 문구 (제목·내용은 전송하지 않고 이 문구만 노출)
BUSY_LABEL = os.getenv("BUSY_LABEL", "다른 사람의 일정").strip()
PRIVATE_LABEL = os.getenv("PRIVATE_LABEL", "비공개 일정").strip()
# 마스킹된 블록 색상
MASK_COLOR = "#9b9a97"

# Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "").strip()
NOTION_DATABASE_IDS = _split(os.getenv("NOTION_DATABASE_IDS", ""))
NOTION_DATE_PROPERTY = os.getenv("NOTION_DATE_PROPERTY", "").strip()
