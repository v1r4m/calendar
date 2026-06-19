"""Google 로그인으로 관리자 신원 확인."""
from __future__ import annotations

import os

from flask import session

import config

# 신원 확인용 scope (캘린더 읽기와 별개)
LOGIN_SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email"]

# 로컬 http 루프백 콜백 허용 (운영 https에서는 불필요)
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
# 구글이 요청 scope에 openid를 덧붙여 돌려줘도 에러내지 않도록
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")


def is_admin() -> bool:
    email = session.get("admin_email")
    return bool(email and config.ADMIN_EMAILS and email in config.ADMIN_EMAILS)


def current_email() -> str:
    return session.get("admin_email", "")


def build_flow(redirect_uri: str):
    from google_auth_oauthlib.flow import Flow

    return Flow.from_client_secrets_file(
        config.GOOGLE_CREDENTIALS_FILE,
        scopes=LOGIN_SCOPES,
        redirect_uri=redirect_uri,
    )


def email_from_callback(flow, authorization_response: str) -> str:
    """콜백 URL로 토큰을 교환하고 검증된 이메일을 반환."""
    from google.auth.transport import requests as grequests
    from google.oauth2 import id_token as gid

    flow.fetch_token(authorization_response=authorization_response)
    idinfo = gid.verify_oauth2_token(
        flow.credentials.id_token,
        grequests.Request(),
        config.GOOGLE_CLIENT_ID,
        clock_skew_in_seconds=10,
    )
    return idinfo.get("email", "")
