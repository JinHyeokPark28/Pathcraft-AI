# PathcraftAI - Project State Document

> **Last Updated:** 2025-11-24
> **이 파일은 Claude가 매번 작업 시작 전에 참조해야 합니다**

---

## 1. 프로젝트 개요

- **이름:** PathcraftAI
- **설명:** POE1 빌드 검색 및 AI 분석 시스템
- **플랫폼:** Windows Desktop (WPF .NET 8 + Python 3.12)
- **대상:** POE 한국어 사용자
- **GGG 승인:** OAuth 2.1 공식 승인 (2025-06-07)

---

## 2. 완료된 기능 (Phase 1-6)

### Phase 1: POE OAuth 2.1 ✅
- PKCE 기반 인증
- 토큰 자동 갱신

### Phase 2: 사용자 빌드 분석 ✅
- 캐릭터 아이템 파싱
- poe.ninja 가격 조회
- 업그레이드 추천

### Phase 3: YouTube 빌드 검색 ✅
- 40+ 영어 / 11 한국어 스트리머
- POB 링크 자동 추출

### Phase 4: 아이템 가격 시스템 ✅
- poe.ninja 캐싱 (1시간 TTL)
- POE Trade URL 생성

### Phase 5: 고급 기능 ✅
- 한국어 번역 (5,847 아이템 + 21,389 스탯)
- POB 파싱 개선
- 북마크 시스템

### Phase 6: LLM 시스템 ✅
- OpenAI/Claude/Gemini 지원
- AI 빌드 가이드 생성

### Phase 7: 파밍 전략 시스템 ✅ (NEW)
- 리그 페이즈 가이드 (early/mid/late)
- poe.ninja 실시간 가격 연동
- 동적 ROI 기반 스카랍 조합 추천
- 15개 파밍 메카닉 상세 데이터

---

## 3. 현재 핵심 이슈 (Critical)

### 3.1 skill_tag_system.py 하드코딩 문제 ✅ 해결됨
**파일:** `src/PathcraftAI.Parser/skill_tag_system.py`

**해결 완료 (2025-11-22):**
- `SKILL_DATABASE` - gems.json에서 338개 액티브 스킬 동적 로드
- `LEVELING_SKILLS_BY_TAG` - 동적 메서드로 변경 (`get_leveling_skills_by_tag`)
- `game_data_fetcher.py`의 `extract_skill_gems()` 개선 - 태그, 스탯 요구사항 추출

**남은 작업:**
- required_level 데이터 (퀘스트 보상에서 가져오기)
- `generate_leveling_guide_summary()` - 아직 하드코딩된 팁 사용

### 3.2 레벨링 가이드 부정확 ✅ 해결됨
**문제:**
- 스킬젬 획득 레벨 부정확
- 퀘스트 보상 정보 없음

**해결 완료 (2025-11-23):**
- poedb.tw 크롤러 작성 (`poedb_crawler.py`)
- quest_rewards.json (128개 퀘스트, 클래스별 보상)
- gem_levels.json (549개 젬 required_level)
- vendor_recipes.json (201개 벤더 레시피)

**코드 개선 (2025-11-23):**
- `get_gem_quest_info()` - required_level 기반 퀘스트 필터링 추가
  - Act별 최대 획득 가능 레벨 검증 (Act1=12, Act2=23, Act3=33...)
  - 레벨 28 젬이 Act 1에서 나오는 등의 오류 방지
- `find_skill_by_name()` - 스킬 이름 매칭 로직 개선
  - Transfigured gem 베이스 이름 매칭 추가
  - 단어 경계 매칭으로 "Arc" ≠ "Arcane" 문제 해결
- `_load_poedb_data()` - Transfigured gem required_level 업데이트
  - "Arc of Oscillating" → "Arc"의 레벨 12 적용

**알려진 이슈:**
- gem_levels.json에서 일부 젬 레벨 부정확 (예: Armageddon Brand=28, 실제=12)
- poedb.tw 데이터 오류 - 추후 수동 검증 필요

### 3.3 필터 생성 오류 ✅ 해결됨
**문제:**
- "알수없는 규칙유형" 에러 보고됨
- POE1 규칙 (HasInfluence, LinkedSockets)은 유효함

**해결 완료 (2025-11-23):**
- `Has{influence}Influence True` → `HasInfluence {influence}` (올바른 형식)
- `HasInfluence "Shaper" "Elder"` → `HasInfluence Shaper Elder` (따옴표 제거)
- `Class "Gems"` → `Class "Skill Gems" "Support Gems"` (올바른 클래스명)
- 3.27 필터 파일 참조하여 NeverSink 형식에 맞게 수정

---

## 4. 데이터 소스 정책

### ✅ 사용 가능
1. **POB 데이터** - 젬/스킬 정보 (최우선)
2. **poe.ninja API** - 가격 정보 (이미 사용 중)
3. **POE 공식 API** - OAuth, 캐릭터 (이미 사용 중)
4. **poedb.tw** - 한국 커뮤니티 DB
5. **GGPK 추출** - 게임 데이터 직접 추출

### ❌ 사용 금지
1. **RePoE** - 업데이트 중단됨 (절대 사용 금지)
2. **PyPoE** - 3년 이상 미관리
3. **POE2 데이터** - POE1만 지원

---

## 5. 데이터 파일 현황

### 사용 중인 파일 (`src/PathcraftAI.Parser/data/`)
```
merged_translations.json      # 한국어 번역 (주요)
awakened_translations.json    # Awakened POE Trade
poe_trade_korean.json        # Trade API 한국어
korean_dat_data.json         # GGPK 추출 데이터
update_cache.json            # 버전 캐시
farming_strategies.json      # 파밍 전략 데이터 (수익, 스카랍 조합)
farming_mechanics.json       # 15개 파밍 메카닉 상세 정보
```

### poedb.tw 크롤링 데이터
```
quest_rewards.json           # 퀘스트 보상 (128개 퀘스트, 클래스별)
gem_levels.json              # 젬 required_level (549개 젬)
vendor_recipes.json          # 벤더 레시피 (201개)
```

### 빌드 전환 패턴 (NEW)
```
build_transition_patterns.json  # Reddit 크롤링 65패턴 (레벨링 → 최종 스킬)
```

### 가이드 템플릿 (`src/PathcraftAI.Parser/data/guide_templates/`)
```
common_template.json              # 공통 레벨링 템플릿
archetype_spell.json              # 스펠 캐스터 아키타입
archetype_attack.json             # 공격 빌드 아키타입
archetype_minion.json             # 소환 빌드 아키타입
archetype_dot.json                # DOT 빌드 아키타입
builds/spell_brand_penance_inquisitor.json  # ZeeBoub Penance Brand 가이드
```

### 게임 데이터 캐시 (`game_data/`)
- base_types.json (24.8MB) - 22,460 베이스 아이템
- poe.ninja 캐시 파일들

### POB 데이터 (NEW - `game_data/`)
```
mods.json              # 13,289개 아이템 모드 (prefix/suffix, 가중치, 태그)
uniques.json           # 1,236개 유니크 아이템 (모드, 레벨 요구, 베이스)
item_bases.json        # 1,061개 베이스 아이템
gems.json              # 552개 스킬젬 (태그, 스탯 요구사항)
essence.json           # 104개 에센스
pantheons.json         # 12개 판테온
cluster_jewels.json    # 클러스터 주얼 설정
```

### POB 저장소 (`pob_repo/`)
- POB GitHub 클론 (git pull로 업데이트)
- `python game_data_fetcher.py --clone` 으로 설치
- `python game_data_fetcher.py --parse-all` 로 JSON 생성

---

## 6. 기술 스택

### Frontend
- WPF (.NET 8 / C#)
- WebView2 (POE Trade 연동)

### Backend
- Python 3.12
- SQLite (북마크)

### 외부 API
- YouTube Data API v3
- poe.ninja API
- POE Official API

---

## 7. 다음 작업 우선순위

### 높음 (이번 주)
1. ~~quest_rewards.json 데이터 구조 수정~~ ✅ 완료
2. ~~레벨링 가이드에 퀘스트 보상 데이터 연동~~ ✅ 완료
3. ~~UI에 필터 생성 기능 통합~~ ✅ 완료 (My Build 탭에서 분석 후 표시)
4. ~~Leveling 3.27 필터 셉터 숨김~~ ✅ 완료 (DoT 빌드용)

### 중간
5. 필터 유효성 검사 및 테스트
6. poe.ninja 가치 규칙 베이스 타입 매핑 개선

### 낮음
7. ~~Electron 모듈 (Stage 3)~~ ✅ 기본 구현 완료
8. 오버레이 UI

---

## 7.1 POE Trade 3단계 (Electron 모듈) ✅

**구현 완료 (2025-11-23):**

**파일 구조:**
```
src/PathcraftAI.Electron/
├── package.json           # 프로젝트 설정, 의존성
├── README.md              # 사용 가이드
└── src/
    ├── main.js            # Electron 메인 프로세스
    └── preload.js         # 보안 브릿지

src/PathcraftAI.UI/
└── ElectronService.cs     # C# IPC 클라이언트
```

**주요 기능:**
- Lazy Loading: 필요시에만 Electron 프로세스 시작
- 메모리 모니터링: 800MB 임계치 초과 시 자동 정리/종료
- 자동 종료: 5분 미사용 시 자동 종료
- 3단계 캐시 시스템: Hot (1분) / Warm (5분) / Cold (30분)
- JSON-RPC IPC: TCP port 47851

**IPC 메서드:**
- `ping`, `show`, `hide`, `navigate`, `search`
- `getMemory`, `getCache`, `clearCache`, `setCache`, `getCacheItem`
- `setLeague`, `shutdown`

**사용법:**
```csharp
var electron = new ElectronService();
await electron.StartAsync();
await electron.SearchAsync("Keepers", itemName: "Headhunter");
```

**설정 (CONFIG):**
- IPC_PORT: 47851
- MEMORY_THRESHOLD_MB: 800
- IDLE_TIMEOUT_MS: 5분
- CACHE_CLEANUP_INTERVAL: 1분

---

## 8. 주요 파일 위치

```
MainWindow.xaml(.cs)         # UI 메인
skill_tag_system.py          # 스킬 태그 (동적 로드)
filter_generator.py          # 필터 생성
GameDataExtractor.cs         # GGPK 추출
Dat64Parser.cs               # DAT64 파싱
poe_ninja_api.py             # 가격 캐싱
farming_strategy_system.py   # 파밍 전략 (poe.ninja 연동)
poedb_crawler.py             # poedb.tw 크롤러 (퀘스트, 젬, 레시피)
game_data_fetcher.py         # POB 데이터 수집 (--clone, --parse-all)
item_recommendation_engine.py # 동적 아이템 추천 (빌드 분석 → 모드 매칭 → 가격 최적화)
build_pattern_crawler.py     # 빌드 전환 패턴 크롤러 (Reddit, GitHub)
```

---

## 9. 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2025-11-24 | Leveling 3.27 필터 셉터 숨김 - Death Aura (Chaos DoT) 빌드용, 레벨링 캐스터 셉터 규칙 Hide |
| 2025-11-24 | build_filter_generator.py 셉터 숨김 로직 추가 - DoT 빌드 타입 감지 시 셉터 Class 규칙 자동 숨김 |
| 2025-11-23 | quest_rewards.json 재구성 - POE Wiki 검증 데이터, 클래스별 정확한 퀘스트 보상 (13개 퀘스트) |
| 2025-11-23 | POE Trade 3단계 Electron 모듈 - Lazy Loading, 메모리 모니터링, 3단계 캐시, JSON-RPC IPC |
| 2025-11-23 | 빌드 전환 패턴 시스템 - Reddit 크롤링 65패턴, 폴백 패턴, 아키타입 분류, 협업 필터링 |
| 2025-11-23 | 동적 아이템 추천 엔진 - POB 빌드 분석 → mods.json 매칭 → poe.ninja 가격 → 예산 최적화 |
| 2025-11-23 | POB 전체 데이터 수집 시스템 - git clone, 모드 13,289개, 유니크 1,236개, 베이스 1,061개 |
| 2025-11-23 | NeverSink 필터 통합 시스템 - 파서, POB 오버레이, poe.ninja 가치 규칙, 7단계 엄격도 |
| 2025-11-23 | 레벨링 가이드 개선 - 태그 기반 젬 진행, 스킬 이름 매칭 강화, 기본 폴백 추가 |
| 2025-11-23 | 필터 생성 HasInfluence 문법 수정, KoreanTranslator skills_kr/items_kr 지원 추가 |
| 2025-11-23 | poedb.tw 크롤러 완성 - 퀘스트 보상 128개, 젬 레벨 549개, 벤더 레시피 201개 |
| 2025-11-23 | 파밍 전략 시스템 완성 - poe.ninja 연동, 현실적 수익 데이터, 15개 메카닉 상세 정보 |
| 2025-11-22 | 4개 아키타입 템플릿 완성 (spell, attack, minion, dot) + 테스트 스크립트 |
| 2025-11-22 | 가이드 템플릿 시스템 추가 - 공통/아키타입 분리, ZeeBoub Penance Brand 가이드 저장 |
| 2025-11-22 | skill_tag_system.py 리팩토링 - POB gems.json에서 338개 스킬 동적 로드 |
| 2025-11-22 | PROJECT_STATE.md, CLAUDE_INSTRUCTIONS.md, CLAUDE.md 생성 |
| 2025-11-22 | 불필요한 파일 삭제 (약 25개) |
| 2025-11-22 | poe.ninja 캐싱, POB 아이템 모드 파싱 |
| 2025-11-21 | 한국어 번역 시스템 (5,847 아이템) |
| 2025-11-21 | 북마크, 설정, 트레이드 윈도우 |
| 2025-11-20 | 사용자 빌드 분석, YouTube 썸네일 |

---

## 10. 작업 시 주의사항

1. **POE1만 지원** - POE2 데이터 사용 금지
2. **RePoE 금지** - 절대 참조하지 말 것
3. **하드코딩 금지** - 데이터는 JSON 파일로 분리
4. **한국어 지원 필수** - 모든 UI/데이터

---

*이 파일은 Claude가 작업을 완료할 때마다 업데이트해야 합니다*
