"""calendar.viram.dev — Notion Calendar 스타일 월간 뷰 (Flask)."""
from __future__ import annotations

from datetime import datetime

import pytz
from flask import Flask, render_template, request

import calendar_grid
import config
from sources import google_calendar, notion_source

app = Flask(__name__)

_KO_MONTH = "{year}년 {month}월"


def _fetch_month_events(year: int, month: int):
    """해당 달 그리드 범위에 걸치는 모든 이벤트를 수집."""
    weeks = calendar_grid.month_range(year, month)
    tz = pytz.timezone(config.TIMEZONE)
    time_min = tz.localize(datetime.combine(weeks[0][0], datetime.min.time()))
    time_max = tz.localize(datetime.combine(weeks[-1][-1], datetime.max.time()))

    events = []
    errors = []
    for name, mod in (("Google", google_calendar), ("Notion", notion_source)):
        try:
            events.extend(mod.fetch(time_min, time_max))
        except Exception as exc:  # 한 소스 실패가 전체를 막지 않도록
            errors.append(f"{name}: {exc}")
    return events, errors


@app.route("/")
def index():
    tz = pytz.timezone(config.TIMEZONE)
    now = datetime.now(tz)
    try:
        year = int(request.args.get("year", now.year))
        month = int(request.args.get("month", now.month))
    except ValueError:
        year, month = now.year, now.month

    # 월 경계 보정
    while month < 1:
        month += 12
        year -= 1
    while month > 12:
        month -= 12
        year += 1

    events, errors = _fetch_month_events(year, month)
    grid = calendar_grid.build(year, month, events)

    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)

    sources_status = {
        "google": google_calendar.is_configured(),
        "notion": notion_source.is_configured(),
    }

    return render_template(
        "index.html",
        grid=grid,
        headers=calendar_grid.weekday_headers(),
        title=_KO_MONTH.format(year=year, month=month),
        year=year,
        month=month,
        today=now.date(),
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
        errors=errors,
        sources_status=sources_status,
        any_configured=any(sources_status.values()),
    )


@app.route("/healthz")
def healthz():
    return {"ok": True}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
