#!/usr/bin/env bash
# calendar 배포 스크립트 (EC2에서 실행). pull → build → up.
# 공용 프록시 eta-caddy 뒤에 붙는다. 최초 1회 eta-caddy Caddyfile 설정은 DEPLOY.md 참고.
set -euo pipefail
cd "$(dirname "$0")"

COMPOSE="docker compose -f docker-compose.prod.yml"

[ -f .env ] || { echo "✗ .env 없음 — 'cp .env.production.example .env' 후 값 채우기" >&2; exit 1; }
[ -f credentials.json ] || { echo "✗ credentials.json 없음 — 로컬에서 복사하세요" >&2; exit 1; }
[ -f token.json ] || { echo "✗ token.json 없음 — 로컬에서 OAuth 로그인 후 생성된 token.json 을 복사하세요" >&2; exit 1; }
# 바인드마운트 대상은 파일이 먼저 있어야 함 (없으면 도커가 디렉터리를 만들어버림)
[ -f categories.json ] || { echo "{}" > categories.json; echo "  ↳ categories.json 생성"; }

echo "▶ 코드 가져오기"
git pull --ff-only || true

echo "▶ 이미지 빌드"
$COMPOSE build

echo "▶ 서비스 기동"
$COMPOSE up -d

echo "✅ 배포 완료."
echo "   최초라면 eta-caddy Caddyfile 에 calendar.viram.dev 블록 추가 후 reload (DEPLOY.md 2-(c))."
echo "   → https://calendar.viram.dev"
