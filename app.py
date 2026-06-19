"""calendar.viram.dev — Notion Calendar 스타일 월간 뷰 (Flask)."""
from __future__ import annotations

from datetime import datetime

import pytz
from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import auth
import calendar_grid
import category_store
import config
from sources import google_calendar, notion_source

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

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


def _category_of(ev, categories: dict[str, str]) -> str:
    """이벤트의 공개 카테고리. Google 일정은 항상 공개, Notion은 저장값/기본값."""
    if ev.source != "notion":
        return "public"
    return categories.get(ev.key, config.DEFAULT_NOTION_CATEGORY)


def _apply_visibility(events, admin):
    """관리자=전부(실제 내용)+카테고리, 뷰어=private 제외·busy 마스킹·public 그대로."""
    categories = category_store.load()
    out = []
    for ev in events:
        cat = _category_of(ev, categories)
        ev.category = cat
        if admin:
            out.append(ev)
            continue
        # ── 뷰어(외부): private/busy는 제목·링크 제거하고 라벨만 노출 ──
        if cat in ("private", "busy"):
            ev.title = config.PRIVATE_LABEL if cat == "private" else config.BUSY_LABEL
            ev.url = ""
            ev.calendar = ""
            ev.color = config.MASK_COLOR
        out.append(ev)
    return out


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

    admin = auth.is_admin()
    preview = request.args.get("preview") == "1"   # 관리자가 외부 화면 미리보기
    effective_admin = admin and not preview
    events = _apply_visibility(events, effective_admin)
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
        is_admin=effective_admin,
        real_admin=admin,
        preview=preview,
        admin_email=auth.current_email(),
        admin_enabled=bool(config.ADMIN_EMAILS),
        cat_labels=config.CATEGORY_LABELS,
        cat_emoji=config.CATEGORY_EMOJI,
    )


# ── 관리자 로그인 (Google 신원 확인) ──────────────────────
@app.route("/login")
def login():
    flow = auth.build_flow(url_for("auth_callback", _external=True))
    auth_url, state = flow.authorization_url(
        access_type="online",
        include_granted_scopes="true",
        prompt="select_account",
    )
    session["oauth_state"] = state
    return redirect(auth_url)


@app.route("/auth/callback")
def auth_callback():
    if not config.ADMIN_EMAILS:
        abort(403, "ADMIN_EMAILS 미설정")
    flow = auth.build_flow(url_for("auth_callback", _external=True))
    try:
        email = auth.email_from_callback(flow, request.url)
    except Exception as exc:
        return render_template("message.html", message=f"로그인 실패: {exc}"), 400

    if email in config.ADMIN_EMAILS:
        session["admin_email"] = email
        return redirect(url_for("index"))
    return (
        render_template(
            "message.html",
            message=f"{email} 은(는) 관리자가 아닙니다. (ADMIN_EMAILS에 없음)",
        ),
        403,
    )


@app.route("/logout")
def logout():
    session.pop("admin_email", None)
    return redirect(url_for("index"))


@app.route("/admin/category", methods=["POST"])
def admin_category():
    if not auth.is_admin():
        abort(403)
    key = request.form.get("key", "")
    category = request.form.get("category", "")
    if not key or category not in config.CATEGORIES:
        abort(400)
    category_store.set_category(key, category)
    return {"key": key, "category": category}


@app.route("/healthz")
def healthz():
    return {"ok": True}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, debug=True)
