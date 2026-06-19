"""소스에 무관한 공통 이벤트 모델."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class Event:
    title: str
    start: datetime          # 표시 시간대로 변환된 aware datetime
    end: datetime
    all_day: bool
    color: str               # CSS 색상 (#hex)
    source: str              # "google" | "notion"
    calendar: str = ""       # 캘린더/DB 이름
    url: str = ""            # 클릭 시 원본으로 이동

    @property
    def start_date(self) -> date:
        return self.start.date()

    @property
    def end_date(self) -> date:
        # 종일 이벤트의 end는 보통 다음날 0시(exclusive)이므로 호출부에서 보정한다.
        return self.end.date()

    def time_label(self) -> str:
        if self.all_day:
            return ""
        h = self.start.hour
        m = self.start.minute
        ampm = "AM" if h < 12 else "PM"
        hh = h % 12 or 12
        return f"{hh}:{m:02d} {ampm}" if m else f"{hh} {ampm}"
