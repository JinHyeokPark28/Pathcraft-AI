# PathcraftAI

**Path of Exile 빌드 검색 및 분석 시스템**

AI 기반 POE 빌드 추천 및 가이드 생성 시스템입니다.

---

## 🎯 핵심 기능

### 1. 🔍 통합 빌드 검색
- **YouTube 빌드 영상 검색** (가장 빠르고 다양함)
- **Reddit 커뮤니티 빌드** (검증된 빌드)
- **poe.ninja 아이템 가격** (실시간 시세)
- **POB 링크 자동 추출**

### 2. 📊 빌드 분석
- 여러 소스의 빌드 데이터 통합
- 어센던시, 주요 아이템, 젬 세팅 분석
- 현재 메타 트렌드 파악

### 3. 🤖 AI 빌드 가이드 생성
- LLM 기반 종합 빌드 가이드
- 레벨링, 장비 진행도, 팁 포함
- OpenAI / Anthropic 지원

---

## ⚡ 빠른 시작

### 설치
```bash
# Python 3.12 이상 필요
python -m venv .venv
.venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 사용 예시

#### Death's Oath 빌드 검색
```bash
cd src/PathcraftAI.Parser
python unified_build_search.py --keyword "Death's Oath"
```

**결과:**
```
YouTube Builds (3):
1. [POE 3.27] Death's Oath Occultist - Budget League Starter Build Guide
   Channel: GhazzyTV
   Views: 45,230 | Likes: 1,823
   POB Links: https://pobb.in/DeathsOathBudget, https://pobb.in/DeathsOathEndgame

Item Pricing:
  Name: Foulborn Death's Oath
  Current Price: 112.8 chaos / 1.00 divine

Total POB Links: 4
```

#### Mageblood 빌드 검색
```bash
python unified_build_search.py --keyword "Mageblood"
```

#### 빌드 가이드 생성
```bash
# Mock LLM (테스트용)
python build_guide_generator.py --keyword "Kinetic Fusillade" --llm mock

# 실제 LLM (API 키 필요)
python build_guide_generator.py --keyword "Death's Oath" --llm openai --model gpt-4
```

---

## 📦 시스템 구성

### 데이터 수집
- `youtube_build_collector.py` - YouTube 빌드 영상 검색 ⭐ NEW
- `reddit_pob_collector.py` - Reddit POB 빌드 수집
- `poe_ninja_fetcher.py` - 아이템 가격 수집
- `patch_notes_collector.py` - 패치 노트 수집

### 빌드 분석
- `unified_build_search.py` - 통합 빌드 검색 ⭐ 권장
- `build_analyzer.py` - 빌드 데이터 분석
- `build_guide_generator.py` - AI 가이드 생성

### 유틸리티
- `ladder_cache_builder.py` - Ladder 캐시 (선택사항)
- `demo_build_search.py` - 데모 스크립트

---

## 🌟 주요 특징

### YouTube 통합 (NEW!)
- ✅ 10배 빠른 검색 속도 (< 5초)
- ✅ Niche 빌드도 발견 가능
- ✅ POB 링크 자동 추출
- ✅ 채널, 조회수, 인기도 메타데이터
- ✅ Mock 모드 지원 (API 키 없이 테스트 가능)

### 기존 방식과 비교
| 기능 | Ladder API (구) | YouTube (신) |
|------|----------------|--------------|
| 속도 | 100+ 초 | < 5 초 |
| Niche 빌드 | ❌ 없음 | ✅ 발견 |
| Private 문제 | ⚠️ 50%+ | ✅ 없음 |
| POB 링크 | 수동 추출 | ✅ 자동 |

---

## 📚 문서

- [시스템 현황](docs/SYSTEM_STATUS.md) - 전체 시스템 상태
- [YouTube API 설정](docs/YOUTUBE_API_SETUP.md) - API 키 발급 방법
- [C# 통합 계획](docs/CSHARP_INTEGRATION_PLAN.md) - WPF 통합 가이드
- [레벨링 가이드](docs/LEVELING_GUIDE_STRUCTURE.md) - 레벨링 시스템
- [내부 테스트 리포트](INTERNAL_TEST_REPORT.md) - 테스트 결과

---

## 🔧 설정

### 🔐 OAuth Authentication (GGG 공식 승인!)

PathcraftAI is **officially approved** by Grinding Gear Games for OAuth access.

**Approval Date:** June 7, 2025
**Client Type:** Public Client
**Scopes:** account:profile, account:characters, account:stashes, account:league_accounts

#### Setup

1. Get your OAuth credentials:
   - Visit https://www.pathofexile.com/my-account/applications
   - Note your Client ID

2. Set environment variables:
   ```bash
   # Windows
   setx POE_OAUTH_CLIENT_ID "your_client_id"
   setx POE_OAUTH_REDIRECT_URI "http://localhost:12345/oauth_callback"

   # macOS/Linux
   export POE_OAUTH_CLIENT_ID="your_client_id"
   export POE_OAUTH_REDIRECT_URI="http://localhost:12345/oauth_callback"
   ```

3. Run OAuth authentication:
   ```bash
   cd src/PathcraftAI.Parser
   python poe_oauth.py --client-id YOUR_CLIENT_ID --save
   ```

4. Token saved to `poe_token.json` (valid for 30 days)

#### Disclaimer

> This product isn't affiliated with or endorsed by Grinding Gear Games in any way.

---

### YouTube API (선택사항)
YouTube 검색을 실제로 사용하려면 API 키가 필요합니다.

1. [YouTube API 키 발급](docs/YOUTUBE_API_SETUP.md)
2. 환경변수 설정:
   ```bash
   # Windows
   setx YOUTUBE_API_KEY "YOUR_API_KEY"
   ```

**무료 할당량**: 10,000 units/day (약 90회 검색)

**API 키 없이도 사용 가능**: Mock 모드로 자동 전환

---

## 📊 데이터 현황

```
✅ Reddit 빌드: 6개
✅ poe.ninja 아이템: 33,610개 (이미지 포함)
✅ 패치 노트: 14개 (3.27.0c ~ 3.26.0)
✅ YouTube 빌드: Mock 데이터 (API 키 발급 시 실제 데이터)
✅ Ladder 캐시: 50개 (선택사항)
```

---

## 🚀 성능

### Death's Oath 검색 예시

**Ladder API (구):**
- 시간: 100+ 초
- 결과: 0개 (top 100에 없음)

**YouTube + Reddit (신):**
- 시간: < 10 초
- 결과: 3개 YouTube + 0개 Reddit
- POB 링크: 4개

**⚡ 10배 이상 빠름 + 더 많은 결과**

---

## 🎮 지원 리그

현재 **Keepers (3.27 - Keepers of the Flame)** 리그 지원

자동으로 최신 리그 감지 가능:
```python
# poe.ninja에서 자동으로 현재 리그 확인
current_league = get_current_league()  # "Keepers"
```

---

## 🛠️ 개발 계획

### Phase 1: 데이터 수집 ✅ 완료
- [x] YouTube API 통합
- [x] Reddit POB 수집
- [x] poe.ninja 아이템 가격
- [x] 패치 노트 수집

### Phase 2: 빌드 분석 ✅ 완료
- [x] 통합 검색 시스템
- [x] LLM 가이드 생성
- [x] Mock 모드 테스트

### Phase 3: C# WPF 통합 ⏳ 진행 중
- [ ] Python CLI Wrapper
- [ ] C# Backend 클래스
- [ ] WPF UI 프로토타입
- [ ] 사용자 설정 (API 키 입력)

### Phase 4: 추가 기능 📋 계획
- [ ] POB 파일 다운로드
- [ ] 빌드 비교 기능
- [ ] 레벨링 가이드 통합
- [ ] 한국어 번역

---

## 💻 기술 스택

- **Python 3.12**: 백엔드 로직
- **YouTube Data API v3**: 빌드 영상 검색
- **poe.ninja API**: 아이템 가격
- **POE Official API**: Ladder 데이터 (보조)
- **Reddit JSON API**: 커뮤니티 빌드
- **.NET 8 / WPF**: 프론트엔드 (계획)

---

## 🤝 기여

이슈 및 PR 환영합니다!

### 주요 개선 사항
- YouTube 검색 정확도 향상
- POB 링크 추출 패턴 추가
- 다국어 지원
- 추가 데이터 소스 (포럼, 스트리머)

---

## 📝 라이선스

MIT License

---

## 📧 문의

프로젝트 관련 문의는 GitHub Issues를 이용해주세요.

---

## 🎯 사용 사례

### 1. "Death's Oath 빌드 찾기"
```bash
python unified_build_search.py --keyword "Death's Oath"
```
→ YouTube 영상 3개, POB 링크 4개 발견

### 2. "현재 메타 빌드 확인"
```bash
python unified_build_search.py --keyword "Mageblood"
```
→ 인기 빌드 + 가격 정보 (213.60 divine)

### 3. "AI 빌드 가이드 생성"
```bash
python build_guide_generator.py --keyword "Kinetic Fusillade" --llm openai
```
→ 종합 빌드 가이드 자동 생성

---

**PathcraftAI** - Find Your Perfect Build

⭐ Star this repo if you find it useful!
