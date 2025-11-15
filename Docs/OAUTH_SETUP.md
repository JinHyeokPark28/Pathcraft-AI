# PathcraftAI - POE OAuth 설정 가이드

## 1. POE 개발자 앱 등록

### 단계 1: POE 개발자 포털 접속
1. https://www.pathofexile.com/developer/apps 접속
2. POE 계정으로 로그인

### 단계 2: 새 앱 생성
1. **"New App"** 버튼 클릭
2. 다음 정보 입력:
   ```
   App Name: PathcraftAI
   Redirect URI: http://localhost:8888/callback
   Description: AI-powered POE build recommendation tool
   ```

### 단계 3: Scopes 선택
다음 권한을 선택하세요:
- ✅ `account:profile` - 계정 기본 정보
- ✅ `account:characters` - 캐릭터 목록 및 정보
- ✅ `account:stashes` - 창고 정보 (선택)
- ✅ `account:leagues` - 리그 정보 (선택)

### 단계 4: Client ID & Secret 저장
앱 등록 후 다음 정보를 받게 됩니다:
- **Client ID**: `your_client_id_here`
- **Client Secret**: `your_client_secret_here` ⚠️ 절대 공개하지 마세요!

---

## 2. 환경 변수 설정

`.env` 파일에 다음 정보 추가:

```env
# POE OAuth Credentials
POE_CLIENT_ID=your_client_id_here
POE_CLIENT_SECRET=your_client_secret_here
```

---

## 3. OAuth 인증 테스트

### Python 스크립트 실행:

```bash
cd src/PathcraftAI.Parser
.venv/Scripts/python.exe test_oauth.py
```

또는 직접 실행:

```bash
.venv/Scripts/python.exe poe_oauth.py --client-id pathcrafterai --client-secret none --save
```

### 인증 플로우:
1. 로컬 서버 시작 (포트 12345)
2. 브라우저가 자동으로 열림
3. POE 계정으로 로그인
4. PathcraftAI 권한 승인
5. OAuth 2.1 PKCE 기반 토큰 교환
6. `poe_token.json` 파일에 자동 저장

### 실제 성공 출력 예시:
```
================================================================================
POE OAuth Manual Authentication Test (with PKCE)
================================================================================

[0/6] Generating PKCE challenge...
[OK] Code verifier: fvArOO_96tbasf25bJCu...
[OK] Code challenge: e8oWhkL9oebuVbD59Hem...

[1/6] Starting local server on port 12345...
[OK] Server started

[2/6] Generating authorization URL...
[OK] Authorization URL: https://www.pathofexile.com/oauth/authorize?...

[3/6] Opening browser...
[OK] Browser opened

[4/6] Waiting for authorization callback...
[OK] Received authorization code: d93ac931a4ce30bfe2a7...

[5/6] Exchanging authorization code for access token...
[DEBUG] Response status: 200
[OK] Access token received!
     Username: ShovelMaker#6178
     Scopes: account:profile account:leagues account:characters account:stashes
     Expires in: 36000 seconds (10 hours)

[OK] Token saved to: C:\...\poe_token.json

================================================================================
Testing API Calls
================================================================================

[TEST 1] Fetching profile...
[OK] Profile UUID: 99b32bc7-0839-43e6-9054-8c583aa65cd0
     Username: ShovelMaker#6178
     Realm: pc
     Twitch: vnddns999

[TEST 2] Fetching characters...
[OK] Total characters: 15

Top 5 characters:
  1. Shovel_Cats - Lv99 Occultist (Standard)
  2. Witch_Shovel - Lv98 Elementalist (Standard)
  3. ANC_Hierophant - Lv97 Hierophant (Standard)
  4. Shovel_KB - Lv95 Warden (Standard)
  5. Shovel_Spectre - Lv93 Necromancer (Keepers) [CURRENT]

================================================================================
SUCCESS! OAuth authentication completed!
================================================================================
```

---

## 4. C# UI 통합

### 인증 버튼 추가:
UI에 "Connect POE Account" 버튼 추가 예정

### 플로우:
1. 사용자가 버튼 클릭
2. Python OAuth 스크립트 실행
3. 브라우저에서 인증 완료
4. 토큰 저장
5. UI에 "Connected: Username" 표시
6. 자동 추천 시 사용자 캐릭터 정보 활용

---

## 5. 보안 주의사항

⚠️ **절대 공개하면 안 되는 정보:**
- Client Secret
- Access Token
- Refresh Token

✅ **안전한 저장:**
- `.env` 파일 (`.gitignore`에 추가됨)
- `poe_token.json` (로컬에만 저장)

---

## 6. Token 갱신

Access Token은 10시간 후 만료됩니다. Refresh Token을 사용해 자동 갱신 가능:

```python
from poe_oauth import refresh_access_token

new_token = refresh_access_token(client_id, client_secret, refresh_token)
```

---

## 문제 해결

### 브라우저가 안 열릴 때:
수동으로 URL 복사해서 브라우저에 붙여넣기

### Cloudflare 403 Forbidden 에러:
브라우저처럼 보이도록 User-Agent 헤더 추가됨:
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8'
}
```

### "Invalid redirect_uri" 에러:
POE 개발자 포털에서 Redirect URI가 정확히 `http://localhost:12345/oauth_callback`인지 확인

### 포트 12345가 이미 사용 중:
다른 프로그램 종료 또는 `poe_oauth.py`에서 `REDIRECT_PORT` 변경

### "Authorization code expired" 에러:
Authorization code는 일회용이며 즉시 사용해야 합니다. 전체 OAuth flow를 다시 실행하세요.

---

## 다음 단계

✅ OAuth 인증 완료
⬜ UI에 계정 연동 버튼 추가
⬜ 사용자 캐릭터 기반 추천 시스템
⬜ 메인 캐릭터 자동 감지
⬜ 리그 변경 자동 추적
