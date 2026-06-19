# calendar.viram.dev
* Google Calendar + Notion Calendar
* for my own service
* mobile friendly & Security

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