# PathcraftAI - Project State Document

> **Last Updated:** 2025-11-22
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

### 3.2 레벨링 가이드 부정확
**문제:**
- 스킬젬 획득 레벨 부정확
- 퀘스트 보상 정보 없음

**해결 방향:**
- POB 데이터 또는 poedb.tw에서 정확한 데이터 추출

### 3.3 필터 생성 오류
**문제:**
- "알수없는 규칙유형" 에러 보고됨
- POE1 규칙 (HasInfluence, LinkedSockets)은 유효함

**해결 방향:**
- 에러 원인 조사 필요

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
```

### 필요하지만 없는 파일
```
quest_rewards.json           # 퀘스트 보상
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
1. skill_tag_system.py를 POB 데이터 기반으로 리팩토링
2. 젬 데이터 JSON 파일 생성
3. 레벨링 가이드 정확도 개선

### 중간
4. 필터 생성 에러 조사
5. GGPK DAT64 파싱 완성

### 낮음
6. Electron 모듈 (Stage 3)
7. 오버레이 UI

---

## 8. 주요 파일 위치

```
MainWindow.xaml(.cs)         # UI 메인
skill_tag_system.py          # 스킬 태그 (수정 필요)
filter_generator.py          # 필터 생성
GameDataExtractor.cs         # GGPK 추출
Dat64Parser.cs               # DAT64 파싱
poe_ninja_api.py             # 가격 캐싱
```

---

## 9. 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
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
