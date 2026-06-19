# calendar.viram.dev

Notion Calendar에서 보던 화면을 그대로 보여주는 개인용 월간 캘린더 (Flask).
Notion Calendar는 자체 데이터가 없고 **Google Calendar + Notion 데이터베이스**를 합쳐
보여주는 앱이라, 이 프로젝트도 두 소스를 같은 월간 그리드에 통합한다.

## 빠른 시작 (로컬)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # 처음 한 번
flask --app app run --port 5000
# http://127.0.0.1:5000
```

자격증명을 아직 안 넣었어도 빈 월간 그리드가 뜬다. 아래대로 채우면 일정이 표시된다.

## Google Calendar 연결

1. [Google Cloud Console](https://console.cloud.google.com/) → 프로젝트 생성
2. **APIs & Services → Library**에서 *Google Calendar API* 사용 설정
3. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   - Application type: **Desktop app**
   - 만든 JSON을 내려받아 프로젝트 루트에 `credentials.json` 으로 저장
4. (테스트 모드면) OAuth consent screen의 **Test users**에 본인 이메일 추가
5. 앱을 처음 실행하면 브라우저로 로그인 창이 뜨고, 동의하면 `token.json` 이 자동 생성됨
   - 특정 캘린더만 보고 싶으면 `.env`의 `GOOGLE_CALENDAR_IDS`에 콤마로 ID 입력
   - 비워두면 연결된 **모든 캘린더**를 색상 그대로 가져온다

## Notion 연결

1. [notion.so/my-integrations](https://www.notion.so/my-integrations) → **New integration** (Internal)
2. 발급된 토큰(`secret_...` 또는 `ntn_...`)을 `.env`의 `NOTION_TOKEN`에 입력
3. 일정으로 쓸 데이터베이스 페이지 → 우측 상단 `···` → **Connections → 내 integration 추가**
4. 데이터베이스 ID를 `.env`의 `NOTION_DATABASE_IDS`에 입력 (여러 개면 콤마 구분)
   - URL `notion.so/<workspace>/<32자 ID>?v=...` 에서 32자 부분이 DB ID
   - 날짜 속성 이름은 `NOTION_DATE_PROPERTY`로 지정, 비우면 첫 date 속성 자동 사용

## 설정 (.env)

| 변수 | 설명 |
|------|------|
| `WEEK_START` | `sunday`(기본) / `monday` |
| `TIMEZONE` | 표시 시간대, 기본 `Asia/Seoul` |
| `PORT` | 개발 서버 포트, 기본 `5000` |
| `GOOGLE_CREDENTIALS_FILE` | OAuth 데스크톱 클라이언트 JSON 경로 |
| `GOOGLE_CALENDAR_IDS` | 특정 캘린더만 (비우면 전체) |
| `NOTION_TOKEN` | Notion 내부 통합 토큰 |
| `NOTION_DATABASE_IDS` | 표시할 DB ID (콤마 구분) |

## 구조

```
app.py              Flask 라우트 (월간 뷰 / healthz)
calendar_grid.py    월 → 주 단위 그리드 + 날짜별 이벤트 버킷
config.py           .env 로딩
sources/
  event.py            공통 이벤트 모델
  google_calendar.py  Google Calendar API (OAuth 데스크톱)
  notion_source.py    Notion 데이터베이스 쿼리
templates/index.html  월간 그리드 마크업
static/style.css      Notion Calendar 스타일 UI
```

## 다음 단계 (배포)

로컬에서 확인되면 calendar.viram.dev로 배포:
- WSGI 서버(gunicorn 등) + 리버스 프록시(nginx/caddy) + HTTPS
- `credentials.json` / `token.json` / `.env` 는 서버에만 두고 절대 커밋하지 않음 (`.gitignore` 처리됨)
- 개인용이므로 앞단에 기본 인증(basic auth)이나 Cloudflare Access 등으로 보호 권장
