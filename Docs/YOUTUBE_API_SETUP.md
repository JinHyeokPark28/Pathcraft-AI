# YouTube API 설정 가이드

PathcraftAI에서 YouTube 빌드 검색을 사용하기 위한 설정 가이드입니다.

## 1. YouTube API 키 발급

### Step 1: Google Cloud Console 접속
1. https://console.cloud.google.com 접속
2. Google 계정으로 로그인

### Step 2: 프로젝트 생성
1. 상단 프로젝트 선택 드롭다운 클릭
2. "새 프로젝트" 클릭
3. 프로젝트 이름: `PathcraftAI` (원하는 이름)
4. "만들기" 클릭

### Step 3: YouTube Data API v3 활성화
1. 왼쪽 메뉴에서 "API 및 서비스" > "라이브러리" 클릭
2. 검색창에 "YouTube Data API v3" 입력
3. "YouTube Data API v3" 클릭
4. "사용 설정" 버튼 클릭

### Step 4: API 키 생성
1. 왼쪽 메뉴에서 "API 및 서비스" > "사용자 인증 정보" 클릭
2. 상단 "+ 사용자 인증 정보 만들기" 클릭
3. "API 키" 선택
4. API 키가 생성됨 (예: `AIzaSyC-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
5. **보안을 위해 "키 제한"을 클릭하여 제한 설정 권장:**
   - API 제한: "YouTube Data API v3"만 선택
   - 애플리케이션 제한: IP 주소 또는 HTTP 리퍼러 설정

### Step 5: 할당량 확인
- 무료 할당량: **10,000 units/day**
- 검색 1회: ~100 units
- 비디오 정보 1개: ~1 unit
- **하루 약 90-100회 검색 가능**

## 2. API 키 설정

### Option 1: 환경변수 설정 (권장)

**Windows:**
```cmd
setx YOUTUBE_API_KEY "AIzaSyC-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**PowerShell:**
```powershell
[System.Environment]::SetEnvironmentVariable('YOUTUBE_API_KEY', 'AIzaSyC-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 'User')
```

**확인:**
```cmd
echo %YOUTUBE_API_KEY%
```

### Option 2: 직접 인자로 전달
```bash
python youtube_build_collector.py --keyword "Death's Oath" --api-key "YOUR_API_KEY"
```

## 3. 필수 패키지 설치

```bash
pip install google-api-python-client
```

## 4. 사용 예시

### 단독 실행
```bash
# 환경변수 사용
python youtube_build_collector.py --keyword "Death's Oath" --league 3.27

# API 키 직접 입력
python youtube_build_collector.py --keyword "Mageblood" --api-key "YOUR_KEY"
```

### 통합 검색 (권장)
```bash
python unified_build_search.py --keyword "Kinetic Fusillade"
```

## 5. API 할당량 관리

### 할당량 사용량 계산
```
검색 요청 (search.list): 100 units
비디오 정보 (videos.list): 1 unit per video

예시: 10개 결과 검색
- 검색: 100 units
- 비디오 정보 10개: 10 units
- 총합: 110 units

하루 10,000 units / 110 = 약 90회 검색 가능
```

### 할당량 초과 시
1. **Mock 모드로 자동 전환**: API 키가 없거나 할당량 초과 시 자동으로 테스트 데이터 사용
2. **유료 플랜 고려**: Google Cloud 유료 플랜으로 업그레이드 가능
3. **캐싱 활용**: 동일 검색어는 캐시 파일 재사용

## 6. 보안 주의사항

### ⚠️ API 키 보안
- **절대 GitHub에 커밋하지 마세요**
- `.gitignore`에 API 키 파일 추가
- 환경변수 사용 권장
- 키 제한 설정 필수

### .gitignore 추가
```
# API Keys
.env
*.key
config/api_keys.json
```

### API 키 회전
정기적으로 API 키 재생성 권장 (3-6개월마다)

## 7. 비용

### 무료 할당량
- **하루 10,000 units** 무료
- 개인 사용자에게 충분

### 유료 플랜
- 10,000 units 초과 시: **$0.001 per unit** (약 1,000원/100,000 units)
- 대부분의 경우 무료 할당량으로 충분

## 8. 문제 해결

### "YOUTUBE_API_KEY not found"
- 환경변수가 제대로 설정되지 않음
- 터미널 재시작 필요
- `echo %YOUTUBE_API_KEY%`로 확인

### "quotaExceeded" 오류
- 하루 할당량 10,000 units 초과
- 다음 날 자정(PST 기준)에 리셋
- Mock 모드로 자동 전환됨

### "API key not valid" 오류
- API 키가 잘못됨
- YouTube Data API v3가 활성화되지 않음
- API 키 제한 설정 확인

## 9. 대안 (API 키 없이 사용)

API 키 없이도 시스템은 정상 작동합니다:

1. **Mock 데이터**: 테스트용 가상 데이터 사용
2. **Reddit 빌드**: Reddit에서 수집한 POB 링크 사용
3. **Ladder 캐시**: POE 공식 래더 데이터 사용
4. **poe.ninja**: 아이템 가격 정보는 API 키 불필요

Mock 모드에서도 시스템 동작을 완전히 검증할 수 있습니다.

## 10. 프로덕션 배포

### C# WPF 통합 시
```csharp
// C# 환경변수 읽기
string apiKey = Environment.GetEnvironmentVariable("YOUTUBE_API_KEY");

// Python 프로세스 실행
var args = $"--keyword \"{keyword}\" --league {league}";
if (!string.IsNullOrEmpty(apiKey))
{
    args += $" --api-key \"{apiKey}\"";
}

var result = await ExecutePython("youtube_build_collector.py", args);
```

### 사용자 설정 UI
WPF 설정 창에서 사용자가 API 키를 입력하고 저장할 수 있도록 구현 권장.

---

**요약:**
- YouTube API 키는 선택사항
- 무료 할당량으로 충분함 (하루 90회 검색)
- API 키 없이도 Mock 모드로 테스트 가능
- 실제 서비스 시 API 키 발급 권장
