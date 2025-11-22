# Claude Instructions for PathcraftAI

> **이 파일은 Claude가 매 세션 시작 시 반드시 읽어야 합니다**

---

## 제1 지침: 작업 시작 전 필수 확인

```
매번 작업을 시작하기 전에:
1. PROJECT_STATE.md 읽기 - 현재 프로젝트 상태 파악
2. BACKLOG.md 확인 - 우선순위 파악
3. 최근 git log 확인 - 변경 이력 파악
```

---

## 절대 금지 사항

### 1. RePoE 사용 금지
```
❌ RePoE GitHub 참조 금지
❌ RePoE 데이터 다운로드 금지
❌ RePoE 기반 코드 작성 금지

이유: 업데이트 중단됨 (3년+ 미관리)
```

### 2. POE2 데이터 금지
```
❌ POE2 API 사용 금지
❌ POE2 게임 데이터 금지
❌ POE2 전용 기능 금지

이유: PathcraftAI는 POE1 전용
```

### 3. 하드코딩 금지
```
❌ 스킬 데이터를 코드에 직접 작성 금지
❌ 레벨링 정보를 코드에 직접 작성 금지

대신: JSON 파일로 분리하여 동적 로드
```

### 4. 외부 크롤링 데이터 신뢰 금지
```
❌ 검증 없이 크롤링 데이터 사용 금지
❌ 출처 불명 데이터 사용 금지

대신: POB, poe.ninja, POE 공식 API 우선
```

---

## 데이터 소스 우선순위

```
1순위: POB 자체 데이터 (젬, 스킬, 아이템)
2순위: poe.ninja API (가격, 빌드 통계)
3순위: POE 공식 API (캐릭터, OAuth)
4순위: poedb.tw (한국 커뮤니티)
5순위: GGPK 직접 추출 (게임 데이터)

사용 금지: RePoE, PyPoE
```

---

## 작업 완료 시 필수 사항

### 1. PROJECT_STATE.md 업데이트
- 새로운 기능 추가 시 "완료된 기능" 섹션 업데이트
- 이슈 해결 시 "현재 핵심 이슈" 섹션 업데이트
- 변경 이력에 오늘 날짜와 내용 추가

### 2. 코드 품질
- 한국어 주석 또는 docstring 추가
- 타입 힌트 사용 (Python)
- 에러 처리 포함

### 3. 테스트
- 새 기능은 기본 테스트 포함
- 기존 기능 깨지지 않았는지 확인

---

## 현재 핵심 이슈 (즉시 해결 필요)

### 1. skill_tag_system.py 리팩토링
```
위치: src/PathcraftAI.Parser/skill_tag_system.py
문제: SKILL_DATABASE에 15개 스킬만 하드코딩
해결: POB 데이터에서 모든 젬 정보 로드
```

### 2. 레벨링 가이드 정확도
```
문제: 젬 획득 레벨, 퀘스트 보상 부정확
해결: POB 또는 poedb.tw에서 정확한 데이터 추출
```

### 3. 불필요한 파일 정리
```
문제: data 폴더에 사용하지 않는 파일 존재
해결: 사용 여부 확인 후 삭제
```

---

## 파일 구조 이해

### 핵심 파일
```
src/PathcraftAI.Parser/
├── skill_tag_system.py      # 스킬 태그 (수정 필요!)
├── filter_generator.py      # 필터 생성
├── poe_ninja_api.py         # 가격 캐싱
├── unified_build_search.py  # 빌드 검색
└── data/                    # 데이터 파일

src/PathcraftAI.Core/
├── GameDataExtractor.cs     # GGPK 추출
├── Dat64Parser.cs           # DAT64 파싱
└── KoreanDatExtractor.cs    # 한국어 추출

src/PathcraftAI.UI/
├── MainWindow.xaml(.cs)     # 메인 UI
└── *.xaml                   # 기타 윈도우
```

### 데이터 파일
```
사용 중:
- merged_translations.json   # 한국어 번역
- awakened_translations.json # Awakened 데이터
- poe_trade_korean.json      # Trade 한국어

필요하지만 없음:
- gems.json                  # 젬 데이터
- quest_rewards.json         # 퀘스트 보상
```

---

## 빌드 및 실행

### 빌드
```bash
dotnet build PathcraftAI.sln
```

### 실행
```bash
# UI 실행
src/PathcraftAI.UI/bin/Debug/net8.0-windows/PathcraftAI.UI.exe

# Python 스크립트
.venv/Scripts/python script_name.py
```

---

## 연락처 및 참고

- **POE 공식 API 문서:** https://www.pathofexile.com/developer/docs
- **poe.ninja API:** https://poe.ninja/api
- **POE Trade API:** https://www.pathofexile.com/trade

---

*이 파일은 프로젝트 정책이 변경될 때 업데이트해야 합니다*
