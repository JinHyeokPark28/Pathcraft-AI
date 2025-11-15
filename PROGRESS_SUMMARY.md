# PathcraftAI - 개발 진행 상황 요약

**마지막 업데이트**: 2025-01-16
**현재 상태**: Phase 4 완료, Phase 5 준비 중

---

## ✅ 완료된 작업

### Phase 1: POE OAuth 2.1 인증 시스템
- [x] PKCE 기반 OAuth 2.1 구현 (`poe_oauth.py`)
- [x] POE 계정 연동 (scopes: account:profile, account:characters, account:stashes, account:leagues)
- [x] 토큰 저장 및 자동 갱신
- [x] UI 연동 ("Connect POE Account" 버튼)
- [x] 로컬 서버 기반 콜백 처리 (localhost:12345)

**주요 파일**:
- `src/PathcraftAI.Parser/poe_oauth.py` - OAuth 인증 로직
- `Docs/OAUTH_SETUP.md` - OAuth 설정 가이드

### Phase 2: 사용자 빌드 분석 엔진
- [x] 캐릭터 아이템 데이터 파싱
- [x] 유니크 아이템 추출 및 분석
- [x] 6링크 감지 및 메인 스킬 파악
- [x] 빌드 타입 자동 추론 (유니크 > 스킬 > 클래스)
- [x] POE.Ninja 기반 아이템 가치 계산
- [x] 빌드별 맞춤 업그레이드 제안

**주요 파일**:
- `src/PathcraftAI.Parser/analyze_user_build.py` - 빌드 분석 엔진
- `src/PathcraftAI.Parser/poe_oauth.py` - 캐릭터 데이터 API

**버그 수정**:
- ✅ Privacy 설정 문제 (아이템 0개) → `equipment` 필드 사용으로 해결
- ✅ 유니크 아이템 이름 추출 (`name` vs `typeLine`)

### Phase 3: UI 통합
- [x] "Your Current Build" 섹션 추가 (MainWindow.xaml)
- [x] 빌드 정보 표시 (캐릭터, 빌드 타입, 스킬, 아이템 가치)
- [x] 업그레이드 제안 표시
- [x] 조건부 UI 표시 (데이터 없으면 숨김)

**주요 파일**:
- `src/PathcraftAI.UI/MainWindow.xaml` (라인 79-138)
- `src/PathcraftAI.UI/MainWindow.xaml.cs` (라인 226-284)

### Phase 4: POE.Ninja 시장 데이터 수집
- [x] poe.ninja API 연동
- [x] 33,831개 아이템 가격 데이터 수집
  - 767 유니크 무기
  - 897 유니크 방어구
  - 333 유니크 악세서리
  - 7,163 스킬 젬
  - 22,460 베이스 타입
- [x] 자동 이미지 다운로드
- [x] 실시간 가격 조회 시스템

**주요 파일**:
- `src/PathcraftAI.Parser/poe_ninja_fetcher.py`
- `src/PathcraftAI.Parser/game_data/` (데이터 저장 폴더)

### Phase 5: 스마트 빌드 분석기 (신규!)
- [x] POB 키스톤 패시브 감지
- [x] 방어 메커니즘 분석 (CI, EB, MoM, Life-based)
- [x] 실시간 시장 가격 기반 장비 평가
- [x] 빌드 특성에 맞는 맞춤형 판테온 추천
  - CI 빌드 → Shakari 제외 추천
  - Life 빌드 → Shakari 포함 추천

**주요 파일**:
- `src/PathcraftAI.Parser/smart_build_analyzer.py`

**키스톤 감지 목록**:
- Chaos Inoculation (CI)
- Eldritch Battery (EB)
- Mind Over Matter (MoM)
- Pain Attunement (Low Life)
- Elemental Equilibrium
- Avatar of Fire
- Acrobatics
- Resolute Technique
- Point Blank
- Vaal Pact
- 등...

---

## 🔧 개발 도구 및 스크립트

### 빌드 분석 도구
1. **`quick_analyze.py`** - 현재 캐릭터 빠른 분석
   - 장비, 스킬, 소켓 구성 확인
   ```bash
   .venv/Scripts/python.exe quick_analyze.py
   ```

2. **`parse_pob.py`** - POB 링크 파싱
   - POB URL에서 빌드 정보 추출
   ```bash
   .venv/Scripts/python.exe parse_pob.py
   ```

3. **`analyze_pob_tree.py`** - 패시브 트리 비교
   - POB vs 현재 캐릭터 패시브 비교
   ```bash
   .venv/Scripts/python.exe analyze_pob_tree.py
   ```

4. **`smart_build_analyzer.py`** - 종합 빌드 가이드
   - 키스톤, 판테온, 장비, 가격 분석
   ```bash
   .venv/Scripts/python.exe smart_build_analyzer.py
   ```

5. **`full_build_guide.py`** - 완전한 빌드 가이드
   - 판테온, 장비, 어센던시, 다음 단계
   ```bash
   .venv/Scripts/python.exe full_build_guide.py
   ```

### 데이터 수집 도구
1. **`poe_ninja_fetcher.py`** - POE.Ninja 데이터 수집
   ```bash
   # 전체 데이터 수집
   .venv/Scripts/python.exe poe_ninja_fetcher.py --collect --league Keepers

   # 데이터 확인
   .venv/Scripts/python.exe poe_ninja_fetcher.py --stats

   # 아이템 분석
   .venv/Scripts/python.exe poe_ninja_fetcher.py --analyze-item "The Taming"
   ```

2. **`popular_build_collector.py`** - YouTube 빌드 수집
   ```bash
   .venv/Scripts/python.exe popular_build_collector.py --league Keepers --version 3.27
   ```

### OAuth 테스트
```bash
.venv/Scripts/python.exe test_oauth.py
```

---

## 📊 실제 사용 사례: Shovel_FuckingWand

### 캐릭터 정보
- **클래스**: Lv69 Elementalist
- **리그**: Keepers
- **빌드**: Kinetic Blast Wander

### 메인 스킬 (6-Link)
- Kinetic Blast
- Returning Projectiles Support
- Trinity Support
- Increased Critical Damage Support
- Summon Sacred Wisps
- Fork Support

### 현재 장비 (실시간 가격)
- Honourhome (헬멧): ~1c
- Prismweave (벨트): ~1c
- Doedre's Tenure (장갑): ~2c
- **The Taming** (반지): ~7c ⭐
- Essence Worm (반지): ~1c

**총 가치**: ~12 chaos (Budget setup)

### POB 목표 빌드
- **URL**: https://pobb.in/L_PjVQbio_WZ
- **레벨**: 94
- **패시브 포인트**: 127개 (현재 98개, 부족 29개)
- **어센던시**: 8포인트 (현재 6포인트)

### 키스톤 패시브
- Elemental Equilibrium
- Avatar of Fire
- Acrobatics

### 추천 판테온
- **Major**: Soul of Lunaris (맵핑) / Soul of Solaris (보스)
- **Minor**: Soul of Shakari (독 면역) / Soul of Gruthkul (물리 감소)

---

## 🎯 주요 기능

### 1. OAuth 기반 사용자 인증
- POE 계정 연동
- 캐릭터 목록 자동 로드
- 토큰 자동 갱신

### 2. 빌드 자동 분석
- 장비 스캔
- 메인 스킬 감지
- 빌드 타입 추론
- 실시간 가격 평가

### 3. POB 통합
- POB 링크 파싱
- 패시브 트리 비교
- 키스톤 감지
- 빌드 가이드 생성

### 4. 시장 데이터
- 실시간 아이템 가격
- 33,000+ 아이템 데이터베이스
- 자동 업데이트

### 5. 맞춤형 추천
- 빌드 특성 기반 판테온 추천
- 키스톤 고려 (CI, EB, MoM 등)
- 가격 기반 업그레이드 제안

---

## 🐛 알려진 이슈

### 해결된 문제
1. ✅ **Privacy 설정으로 아이템 0개**
   - 원인: `items` 대신 `character.equipment` 필드 사용
   - 해결: API 응답 구조 수정

2. ✅ **유니크 아이템 이름 표시 오류**
   - 원인: `typeLine` vs `name` 필드 혼동
   - 해결: 유니크는 `name` 우선 사용

3. ✅ **POE.Ninja 가격 0원**
   - 원인: JSON 구조 `lines` → `items` 변경
   - 해결: 데이터 로드 로직 수정

### 현재 제한사항
1. **Rate Limit**: POE API 429 에러 발생 가능
   - 해결: 요청 간 2-3초 대기

2. **Currency 데이터 없음**
   - POE.Ninja에서 Keepers 리그 Currency 데이터 미제공
   - 다른 리그에서는 정상 작동

3. **YouTube API 키 미설정**
   - `popular_build_collector.py` 실행 불가
   - 베트남에서 API 키 발급 필요

---

## 🏗️ 프로젝트 구조

```
PathcraftAI/
├── src/
│   ├── PathcraftAI.UI/              # WPF UI
│   │   ├── MainWindow.xaml          # 메인 UI
│   │   └── MainWindow.xaml.cs       # UI 로직
│   ├── PathcraftAI.Parser/          # Python 백엔드
│   │   ├── poe_oauth.py             # OAuth 인증
│   │   ├── analyze_user_build.py    # 빌드 분석
│   │   ├── poe_ninja_fetcher.py     # 시장 데이터
│   │   ├── smart_build_analyzer.py  # 스마트 분석기
│   │   ├── quick_analyze.py         # 빠른 분석
│   │   ├── parse_pob.py             # POB 파싱
│   │   ├── analyze_pob_tree.py      # 트리 비교
│   │   ├── full_build_guide.py      # 종합 가이드
│   │   └── game_data/               # 시장 데이터
│   ├── PathcraftAI.Core/            # 공통 로직
│   ├── PathcraftAI.LLM/             # AI 통합
│   ├── PathcraftAI.Storage/         # 데이터 저장
│   └── PathcraftAI.Overlay/         # 게임 오버레이
├── Docs/
│   ├── PRD.md                       # 제품 요구사항
│   └── OAUTH_SETUP.md               # OAuth 가이드
├── NEXT_TASKS.md                    # 다음 작업 목록
└── PROGRESS_SUMMARY.md              # 이 문서
```

---

## 📈 성능 지표

### 데이터 수집
- **아이템 수**: 33,831개
- **이미지 수**: 33,831개
- **수집 시간**: ~5분
- **데이터 크기**: ~500MB (이미지 포함)

### API 응답 시간
- **OAuth 토큰**: ~1초
- **캐릭터 목록**: ~0.5초
- **캐릭터 아이템**: ~1초 (Rate limit 고려)
- **POE.Ninja 데이터**: ~10초 (전체 카테고리)

---

## 🔐 보안 고려사항

### OAuth 토큰 관리
- 토큰 저장 위치: `poe_token.json` (로컬)
- ⚠️ **주의**: 토큰 파일 Git에 업로드 금지
- `.gitignore`에 `poe_token.json` 추가됨

### API 키
- YouTube API 키: 환경변수 또는 `.env` 파일
- POE OAuth Client ID: 코드에 하드코딩 (public)

---

## 📚 참고 문서

### 공식 문서
- [POE OAuth Docs](https://www.pathofexile.com/developer/docs/authorization)
- [POE.Ninja API](https://poe.ninja/api)
- [YouTube Data API](https://developers.google.com/youtube/v3)

### 내부 문서
- [PRD.md](Docs/PRD.md) - 제품 요구사항 문서
- [OAUTH_SETUP.md](Docs/OAUTH_SETUP.md) - OAuth 설정 가이드
- [NEXT_TASKS.md](NEXT_TASKS.md) - 다음 작업 목록

---

## 🎮 테스트 환경

### 개발 환경
- **OS**: Windows 10/11
- **.NET**: 8.0
- **Python**: 3.11+
- **IDE**: Visual Studio Code

### 테스트 계정
- **POE 계정**: ShovelMaker#6178
- **테스트 캐릭터**: Shovel_FuckingWand (Lv69 Elementalist, Keepers)

### 빌드 및 실행
```bash
# C# 빌드
dotnet build

# Python 가상환경 활성화
cd src/PathcraftAI.Parser
.venv/Scripts/activate

# WPF 앱 실행
cd ../..
dotnet run --project src/PathcraftAI.UI
```

---

## 🚀 다음 단계

자세한 내용은 [VIETNAM_TASKS.md](VIETNAM_TASKS.md) 참조
