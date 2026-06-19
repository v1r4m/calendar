"""Google Calendar에서 이벤트를 가져온다 (개인용 OAuth 데스크톱 플로우)."""
from __future__ import annotations

import os
from datetime import datetime, timedelta

import pytz

import config
from sources.event import Event

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Google 기본 색상 ID → hex (calendarList/event의 colorId 매핑 보완용 폴백)
_DEFAULT_COLOR = "#4285F4"


def is_configured() -> bool:
    return os.path.exists(config.GOOGLE_CREDENTIALS_FILE) or os.path.exists(
        config.GOOGLE_TOKEN_FILE
    )


def _get_service():
    """인증된 Calendar API 서비스를 반환. 자격증명 없으면 None."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if os.path.exists(config.GOOGLE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.GOOGLE_TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif os.path.exists(config.GOOGLE_CREDENTIALS_FILE):
            flow = InstalledAppFlow.from_client_secrets_file(
                config.GOOGLE_CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        else:
            return None
        with open(config.GOOGLE_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _parse(dt: dict, tz) -> tuple[datetime, bool]:
    """Google의 start/end dict를 (aware datetime, all_day) 로 변환."""
    if "date" in dt:  # 종일 이벤트
        naive = datetime.strptime(dt["date"], "%Y-%m-%d")
        return tz.localize(naive), True
    raw = dt["dateTime"]  # RFC3339, 오프셋 포함
    parsed = datetime.fromisoformat(raw)
    return parsed.astimezone(tz), False


def fetch(time_min: datetime, time_max: datetime) -> list[Event]:
    """주어진 기간(aware datetime)에 걸치는 이벤트 목록."""
    service = _get_service()
    if service is None:
        return []

    tz = pytz.timezone(config.TIMEZONE)

    # 색상표 (colorId -> hex)
    try:
        colors = service.colors().get().execute()
        event_colors = colors.get("event", {})
        cal_colors = colors.get("calendar", {})
    except Exception:
        event_colors, cal_colors = {}, {}

    # 대상 캘린더 목록
    if config.GOOGLE_CALENDAR_IDS:
        cal_list = [{"id": cid, "summary": cid} for cid in config.GOOGLE_CALENDAR_IDS]
        cal_meta = {}
    else:
        items = service.calendarList().list().execute().get("items", [])
        cal_list = items
        cal_meta = {c["id"]: c for c in items}

    events: list[Event] = []
    for cal in cal_list:
        cal_id = cal["id"]
        meta = cal_meta.get(cal_id, cal)
        default_hex = (
            cal_colors.get(str(meta.get("colorId")), {}).get("background")
            or meta.get("backgroundColor")
            or _DEFAULT_COLOR
        )
        page_token = None
        while True:
            try:
                resp = (
                    service.events()
                    .list(
                        calendarId=cal_id,
                        timeMin=time_min.isoformat(),
                        timeMax=time_max.isoformat(),
                        singleEvents=True,
                        orderBy="startTime",
                        maxResults=2500,
                        pageToken=page_token,
                    )
                    .execute()
                )
            except Exception:
                break

            for item in resp.get("items", []):
                if item.get("status") == "cancelled" or "start" not in item:
                    continue
                start, all_day = _parse(item["start"], tz)
                end, _ = _parse(item["end"], tz)
                hex_color = (
                    event_colors.get(str(item.get("colorId")), {}).get("background")
                    or default_hex
                )
                events.append(
                    Event(
                        title=item.get("summary", "(제목 없음)"),
                        start=start,
                        end=end,
                        all_day=all_day,
                        color=hex_color,
                        source="google",
                        calendar=meta.get("summary", ""),
                        url=item.get("htmlLink", ""),
                        id=item.get("id", ""),
                    )
                )

            page_token = resp.get("nextPageToken")
            if not page_token:
                break

    return events
