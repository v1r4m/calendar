"""월간 그리드 구성 로직."""
from __future__ import annotations

import calendar as _cal
from datetime import date, datetime, timedelta

import pytz

import config
from sources.event import Event


def month_range(year: int, month: int):
    """그리드에 표시할 (첫째 날, 마지막 날) — 앞뒤 달의 채움 날짜 포함."""
    week_start = 6 if config.WEEK_START == "sunday" else 0  # Sun=6, Mon=0
    cal = _cal.Calendar(firstweekday=week_start)
    weeks = cal.monthdatescalendar(year, month)
    return weeks  # list[list[date]] (각 주 7일)


def build(year: int, month: int, events: list[Event]) -> list[list[dict]]:
    """주 단위 2차원 리스트. 각 칸은 {date, in_month, is_today, events}."""
    tz = pytz.timezone(config.TIMEZONE)
    today = datetime.now(tz).date()
    weeks = month_range(year, month)

    # 날짜별 이벤트 버킷
    buckets: dict[date, list[Event]] = {}
    for ev in events:
        start = ev.start_date
        # 종일 이벤트 end는 exclusive(다음날 0시)이므로 하루 빼서 보정
        end = ev.end_date
        if ev.all_day and ev.end > ev.start:
            end = (ev.end - timedelta(seconds=1)).date()
        day = start
        while day <= end:
            buckets.setdefault(day, []).append(ev)
            day += timedelta(days=1)

    def sort_key(e: Event):
        return (0 if e.all_day else 1, e.start)

    grid: list[list[dict]] = []
    for week in weeks:
        row = []
        for d in week:
            day_events = sorted(buckets.get(d, []), key=sort_key)
            row.append(
                {
                    "date": d,
                    "in_month": d.month == month,
                    "is_today": d == today,
                    "events": day_events,
                }
            )
        grid.append(row)
    return grid


def weekday_headers() -> list[str]:
    if config.WEEK_START == "sunday":
        return ["일", "월", "화", "수", "목", "금", "토"]
    return ["월", "화", "수", "목", "금", "토", "일"]
