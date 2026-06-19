"""Notion 데이터베이스의 날짜 속성을 일정으로 가져온다."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytz
import requests

import config
from sources.event import Event

API = "https://api.notion.com/v1"
VERSION = "2022-06-28"

# 멀티데이 일정은 "시작일"이 보는 달 범위보다 앞설 수 있다.
# Notion 필터는 시작일 기준이라, 시작일이 그만큼 과거여도 걸치는 일정을 놓치지 않도록
# 조회 하한을 이만큼 앞당겨 넉넉히 가져온다 (그리드엔 보이는 날짜만 렌더됨).
LOOKBACK_DAYS = 92

# Notion 속성 색상 이름 → hex
_NOTION_COLORS = {
    "default": "#787774",
    "gray": "#787774",
    "brown": "#9F6B53",
    "orange": "#D9730D",
    "yellow": "#CB912F",
    "green": "#448361",
    "blue": "#337EA9",
    "purple": "#9065B0",
    "pink": "#C14C8A",
    "red": "#D44C47",
}


def is_configured() -> bool:
    return bool(config.NOTION_TOKEN and config.NOTION_DATABASE_IDS)


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {config.NOTION_TOKEN}",
        "Notion-Version": VERSION,
        "Content-Type": "application/json",
    }


def _db_meta(db_id: str) -> tuple[str, str]:
    """(DB 제목, 날짜로 쓸 속성 이름) 반환."""
    resp = requests.get(f"{API}/databases/{db_id}", headers=_headers(), timeout=15)
    resp.raise_for_status()
    data = resp.json()

    title = "".join(t.get("plain_text", "") for t in data.get("title", [])) or "Notion"

    date_prop = config.NOTION_DATE_PROPERTY
    if not date_prop:
        for name, prop in data.get("properties", {}).items():
            if prop.get("type") == "date":
                date_prop = name
                break
    return title, date_prop


def _title_of(page: dict) -> str:
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            return "".join(t.get("plain_text", "") for t in prop.get("title", [])) or "(제목 없음)"
    return "(제목 없음)"


def _parse_dt(value: str, tz, end=False) -> tuple[datetime, bool]:
    """Notion 날짜 문자열 → (aware datetime, all_day)."""
    if "T" in value:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = tz.localize(parsed)
        return parsed.astimezone(tz), False
    naive = datetime.strptime(value, "%Y-%m-%d")
    dt = tz.localize(naive)
    return dt, True


def fetch(time_min: datetime, time_max: datetime) -> list[Event]:
    if not is_configured():
        return []

    tz = pytz.timezone(config.TIMEZONE)
    events: list[Event] = []

    for db_id in config.NOTION_DATABASE_IDS:
        try:
            db_title, date_prop = _db_meta(db_id)
        except Exception:
            continue
        if not date_prop:
            continue

        lo = (time_min - timedelta(days=LOOKBACK_DAYS)).date().isoformat()
        payload = {
            "filter": {
                "and": [
                    {"property": date_prop, "date": {"on_or_after": lo}},
                    {"property": date_prop, "date": {"before": time_max.date().isoformat()}},
                ]
            },
            "page_size": 100,
        }
        cursor = None
        while True:
            if cursor:
                payload["start_cursor"] = cursor
            try:
                resp = requests.post(
                    f"{API}/databases/{db_id}/query",
                    headers=_headers(),
                    json=payload,
                    timeout=15,
                )
                resp.raise_for_status()
            except Exception:
                break
            data = resp.json()

            for page in data.get("results", []):
                props = page.get("properties", {})
                date_val = props.get(date_prop, {}).get("date")
                if not date_val or not date_val.get("start"):
                    continue
                start, all_day = _parse_dt(date_val["start"], tz)
                if date_val.get("end"):
                    end, _ = _parse_dt(date_val["end"], tz, end=True)
                    # Notion 종일 범위의 end는 "마지막 날"(포함). Google처럼 배타적(다음날 0시)
                    # 으로 맞춰야 calendar_grid의 마지막날 보정이 옳게 동작한다.
                    if all_day:
                        end = end + timedelta(days=1)
                elif all_day:
                    end = start + timedelta(days=1)
                else:
                    end = start + timedelta(hours=1)

                # 속성 색상 → 이벤트 색 (없으면 파랑)
                color = _NOTION_COLORS.get(
                    (props.get("Status", {}).get("status") or {}).get("color")
                    if props.get("Status", {}).get("type") == "status"
                    else None,
                    "#337EA9",
                )

                events.append(
                    Event(
                        title=_title_of(page),
                        start=start,
                        end=end,
                        all_day=all_day,
                        color=color,
                        source="notion",
                        calendar=db_title,
                        url=page.get("url", ""),
                        id=page.get("id", ""),
                    )
                )

            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")

    return events
