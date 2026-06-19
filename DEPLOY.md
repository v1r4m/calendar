# 배포 가이드 (EC2 + Docker Compose, 공용 프록시 뒤)

`calendar.viram.dev` 에 올리는 절차.

이 EC2엔 이미 **`eta-caddy` 가 80/443 을 점유한 공용 리버스 프록시**로 돌고 있다.
그래서 우리 스택은 호스트 포트를 열지 않고 eta-caddy 와 같은 네트워크에 붙어,
eta-caddy 가 TLS 를 종료하고 `calendar.viram.dev` 를 `http://calendar:5000` 으로 넘긴다.

```
eta-caddy (443, TLS)  →  calendar:5000 (Flask/gunicorn)
```

상태(큐레이션 `categories.json`, 토큰 `token.json`)는 호스트 바인드마운트라 백업이 쉽다.

---

## 0. 사전 준비 (로컬에서)

배포 전에 **로컬에서 Google 로그인을 끝내 `token.json` 을 만들어 둔다** (서버엔 브라우저가 없어 OAuth 창을 못 띄움).
- `credentials.json` (데스크톱 OAuth 클라이언트), `token.json` 두 파일을 서버로 복사할 것.

### Cloudflare DNS
- `calendar` A 레코드 → **EC2 퍼블릭 IP** (다른 도메인과 같은 IP)
- TLS는 eta-caddy(Let's Encrypt)가 처리. 보안그룹 80/443 은 이미 열려 있음(추가 작업 불필요).

---

## 1. 최초 배포

```bash
git clone <레포 URL> calendar && cd calendar

cp .env.production.example .env
nano .env
#  - NOTION_TOKEN / NOTION_DATABASE_IDS 입력
#  - SECRET_KEY 를 긴 랜덤값으로
#  - PROXY_NETWORK 를 eta-caddy 의 네트워크 이름으로 (아래 2번에서 확인)
```

로컬에서 만든 자격증명/토큰을 서버로 복사 (로컬 PC에서 실행):
```bash
scp credentials.json token.json <user>@<EC2-IP>:~/calendar/
```

### 2. 공용 프록시 연동

**(a) eta-caddy 의 네트워크 이름 확인 → `.env` 의 `PROXY_NETWORK` 에 기입**
```bash
docker inspect eta-caddy-1 --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'
# 예: eta_default  →  .env 에  PROXY_NETWORK=eta_default
```

**(b) 배포**
```bash
chmod +x deploy.sh
./deploy.sh
```

**(c) eta-caddy 의 Caddyfile 에 사이트 블록 추가**
먼저 eta-caddy 의 Caddyfile 이 호스트 어디에 마운트됐는지 확인:
```bash
docker inspect eta-caddy-1 --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
```
그 Caddyfile 에 추가:
```
calendar.viram.dev {
    reverse_proxy calendar:5000
}
```
적용(reload):
```bash
docker exec eta-caddy-1 caddy reload --config /etc/caddy/Caddyfile
#  reload 가 안 되면:  docker restart eta-caddy-1
```

→ `https://calendar.viram.dev` 접속 확인.

---

## 3. 이후 업데이트

```bash
./deploy.sh
```
`git pull → build → up` 자동 수행. eta-caddy 설정은 한 번만 하면 됨.

---

## 4. 백업

```bash
cp categories.json ~/backups/calendar-categories-$(date +%F).json
cp token.json      ~/backups/calendar-token-$(date +%F).json
```

---

## 5. (선택) 프로덕션 관리자 Google 로그인

지금 `credentials.json` 은 **데스크톱** OAuth 클라이언트라 루프백(127.0.0.1) 콜백만 허용한다.
따라서 `https://calendar.viram.dev` 에서의 **관리자 Google 로그인은 그대로는 안 된다**
(공개 뷰어 사이트와 캘린더 읽기는 정상 동작 — 토큰은 로컬에서 발급한 걸 쓰므로).

데스크톱 OAuth 클라이언트는 **Application type 을 못 바꾼다 — Web 클라이언트를 새로 발급**해서
서버의 `credentials.json` 을 그걸로 통째로 교체하면 된다.

1. Google Cloud Console → Credentials → Create Credentials → OAuth client ID → **Web application**
2. **Authorized redirect URIs** 에 추가: `https://calendar.viram.dev/auth/callback` (끝 슬래시 없음)
3. 받은 JSON 을 서버의 **`credentials.json`** 으로 덮어쓴다 (scp 로 복사)
4. 그 계정 이메일이 `.env` 의 `ADMIN_EMAILS` 에 있어야 관리자로 인정
5. **컨테이너 재시작** (config 는 시작 시 credentials.json 을 한 번만 읽음):
   ```bash
   docker compose -f docker-compose.prod.yml restart
   ```
6. 확인 — /login 이 새 client_id 를 쓰는지:
   ```bash
   curl -s -o /dev/null -w '%{redirect_url}\n' https://calendar.viram.dev/login | grep -o 'client_id=[^&]*'
   ```

> 캘린더 읽기는 `token.json` 이 자기 안에 (옛) 자격증명을 품고 있어 영향 없다 — credentials.json 을
> Web 클라이언트로 바꿔도 일정은 계속 보인다.
> 당장 로그인이 필요 없으면, 관리자 큐레이션을 **로컬에서** 하고 `categories.json` 만 서버로 복사해도 된다.

---

## 6. 운영 메모 / 트러블슈팅

- **로그**: `docker compose -f docker-compose.prod.yml logs -f`
- **재시작**: `docker compose -f docker-compose.prod.yml restart`

### `external network ... not found`
`.env` 의 `PROXY_NETWORK` 이름이 eta-caddy 의 실제 네트워크와 다르다. 위 2-(a) 로 재확인.

### 502 Bad Gateway (eta-caddy 로그)
eta-caddy 가 `calendar` 컨테이너를 못 찾음. 같은 네트워크에 있는지 확인:
```bash
docker network inspect <PROXY_NETWORK> --format '{{range .Containers}}{{.Name}} {{end}}'
# eta-caddy-1 과 calendar-1 이 모두 보여야 함
```

### ERR_SSL_PROTOCOL_ERROR / `tlsv1 alert internal error` (인증서 없음)
Caddy 가 그 도메인 인증서를 못 내준 상태. 거의 항상 **새 블록이 실행 중인 Caddy 에
실제로 안 올라간 것**이다. `caddy reload` 가 `config is unchanged` 라고 *거짓* 보고하며
새 블록을 무시하는 경우가 있다 — 이때는 **강제 재시작**으로 파일을 처음부터 다시 읽힌다:
```bash
sudo docker restart eta-caddy-1 && sleep 8
sudo docker logs eta-caddy-1 --since 1m 2>&1 | grep -iE "calendar|obtaining|obtained|acme|error"
```
`enabling automatic TLS ... calendar.viram.dev` + `certificate obtained successfully` 가
보이면 성공. (reload 이 안 먹으면 restart — 이게 핵심.)

### 캘린더가 비어 있음
`token.json` 이 서버에 없거나 만료. 로컬에서 재발급 후 다시 복사.
`docker compose -f docker-compose.prod.yml logs` 에서 Google/Notion 에러 확인.
