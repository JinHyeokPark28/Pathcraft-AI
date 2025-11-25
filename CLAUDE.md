# PathcraftAI - Claude Instructions

> **이 파일은 Claude가 자동으로 읽습니다**

## 필수 참조 파일

매 세션 시작 시 반드시 읽어야 할 파일:
1. **PROJECT_STATE.md** - 현재 프로젝트 상태
2. **CLAUDE_INSTRUCTIONS.md** - 상세 지침
3. **BACKLOG.md** - 작업 우선순위

## 핵심 규칙

### 데이터 소스
- ✅ **사용**: POB 데이터, poe.ninja, POE 공식 API, poedb.tw
- ❌ **금지**: RePoE (업데이트 중단), PyPoE

### 프로젝트 범위
- POE1 전용 (POE2 데이터 사용 금지)
- 한국어 지원 필수

### 코딩 규칙
- 하드코딩 금지 → JSON 파일로 분리
- 작업 완료 후 PROJECT_STATE.md 업데이트

## 현재 핵심 이슈

1. ~~**skill_tag_system.py** - 15개 스킬만 하드코딩됨~~ ✅ 해결됨 (338개 스킬 동적 로드)
2. ~~**레벨링 가이드** - 젬 획득 레벨 부정확~~ ✅ 해결됨 (required_level 필터링 추가)
3. ~~**필터 생성** - 일부 규칙 오류~~ ✅ 해결됨 (HasInfluence, Class 문법 수정)

**알려진 이슈 (데이터 품질):**
- gem_levels.json 일부 젬 레벨 부정확 (예: Armageddon Brand=28, 실제=12)
- poedb.tw 데이터 오류 - 수동 검증 필요

자세한 내용은 PROJECT_STATE.md 참조

---

## 중요: 작업 완료 시 반드시 수행

**이슈 해결 후:**
1. 이 파일(CLAUDE.md)의 "현재 핵심 이슈" 섹션에서 해결된 항목 삭제
2. PROJECT_STATE.md의 "현재 핵심 이슈" 섹션 업데이트
3. PROJECT_STATE.md의 "변경 이력" 섹션에 날짜와 내용 추가
4. 새로운 이슈 발견 시 두 파일 모두에 추가

**이것은 수동 작업입니다 - Claude가 직접 해야 합니다**
