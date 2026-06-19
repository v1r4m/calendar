"""최초 1회 Google OAuth 로그인 → token.json 생성."""
from google_auth_oauthlib.flow import InstalledAppFlow

import config
from sources.google_calendar import SCOPES

flow = InstalledAppFlow.from_client_secrets_file(config.GOOGLE_CREDENTIALS_FILE, SCOPES)
creds = flow.run_local_server(port=0, prompt="consent")
with open(config.GOOGLE_TOKEN_FILE, "w") as f:
    f.write(creds.to_json())
print("OK: token.json 생성 완료")
