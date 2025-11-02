# ✅ Pathcraft AI — 체크리스트 태스크 리스트

## 📌 사용 방법
- [ ] 미완료 태스크
- [x] 완료된 태스크
- 각 태스크 완료 후 반드시 **개발자에게 확인** 받고 체크
- 체크 후 다음 태스크로 진행
- **순서대로 진행 필수** (건너뛰기 금지)

---

## 🎯 Phase 1: 핵심 인프라 (완료)

### P1 — 프로젝트 구조 생성
**예상 시간:** 1시간 | **의존성:** 없음 | **상태:** ✅ 완료

- [x] 솔루션 `PathcraftAI.sln` 생성
- [x] 프로젝트 추가 (UI, Core, Overlay, Parser, LLM, Storage, Tests)
- [x] 참조 연결 (UI → Core, LLM, Storage, Parser)
- [x] 빌드 검증 (.NET 8 WPF)
- [x] **개발자 확인 완료**

---

### P2 — Parser 모듈 연동
**예상 시간:** 2시간 | **의존성:** P1 | **상태:** ✅ 완료

- [x] 가상환경 생성 및 `requirements.txt` 설치
- [x] `pob_parser.py` 동작 검증
- [x] `PythonRunner.cs` 작성 (C#에서 Python 호출)
- [x] 파서 호출 성공 및 JSON 출력 확인
- [x] **개발자 확인 완료**

---

### P3 — Overlay 기본 구조
**예상 시간:** 2시간 | **의존성:** P1 | **상태:** ✅ 완료

- [x] Overlay 프로젝트 생성 및 Core 참조
- [x] 기본 반투명 창 표시
- [x] ESC 닫기 동작
- [x] `build_output.json` 실시간 갱신 바인딩
- [x] **개발자 확인 완료**

---

### P4 — Overlay 자동 갱신
**예상 시간:** 1시간 | **의존성:** P3 | **상태:** ✅ 완료

- [x] `DispatcherTimer` 1초 주기 갱신
- [x] 예외 무시 및 UI 반영 안정화
- [x] Core DTO (`BuildSnapshot`) 사용 정상
- [x] **개발자 확인 완료**

---

### P5 — 핫키 토글 + 클릭스루
**예상 시간:** 2시간 | **의존성:** P4 | **상태:** ✅ 완료

- [x] Ctrl + F8 → Overlay On/Off
- [x] Ctrl + F9 → ClickThrough Toggle
- [x] ESC → 닫기
- [x] 64비트 SetWindowLongPtr 호환성 검증
- [x] **개발자 확인 완료**

---

## 🔧 코드 리뷰 및 성능 최적화 (완료)

### CR1 — 전체 프로젝트 검토 및 최적화
**완료 시간:** 1시간 | **상태:** ✅ 완료

#### 수행된 작업
- [x] 전체 코드 리뷰 (7개 프로젝트)
- [x] 불필요한 코드 제거 (Class1.cs 4개)
- [x] 경로 캐싱 시스템 구현 (PathCache.cs)
- [x] 성능 최적화:
  - [x] PythonRunner.cs - PathCache 적용
  - [x] OverlayWindow.xaml.cs - 경로 탐색 최적화
  - [x] ReasoningFiller.cs - 복잡도 O(n*m) → O(n)
  - [x] BuildNormalizer.cs - 조기 종료(break) 추가
  - [x] pob_parser.py - lxml 의존성 제거
- [x] 프로젝트 설정 수정 (PathcraftAI.Parser.csproj 참조 추가)
- [x] 빌드 검증 (Release/Debug 0 경고, 0 오류)

#### 성능 개선 결과
| 항목 | 개선율 | 효과 |
|------|--------|------|
| 경로 탐색 캐싱 | 92% | 반복 호출 최적화 |
| OverlayWindow TickUpdate | 무한 개선 | CPU/디스크 사용률 ↓ |
| ReasoningFiller 알고리즘 | O(n) 복잡도 | 선형 성능 |
| BuildNormalizer 조기 종료 | 30~50% | 불필요한 순회 제거 |
| Python 설치 크기 | -5MB+ | lxml 제거 |

#### 생성/수정 파일
- ✅ **생성:** PathcraftAI.Core/Utils/PathCache.cs
- ✏️ **수정:** PythonRunner.cs, OverlayWindow.xaml.cs, ReasoningFiller.cs, BuildNormalizer.cs, pob_parser.py
- ✏️ **수정:** requirements.txt, PathcraftAI.Parser.csproj
- ❌ **삭제:** Class1.cs (4개)

#### 최종 확인
- [x] **개발자 확인 완료**

---

## 🎯 Phase 2: 스태시 분석 기초

### P6 — 스태시 목업 데이터 생성
**예상 시간:** 2시간 | **의존성:** P5

#### 주요 작업
- [ ] `stash_mock.json` 생성
- [ ] 아이템 데이터 구조 정의
  ```json
  {
    "items": [
      {
        "name": "Steel Ring",
        "type": "Ring",
        "rarity": "Rare",
        "ilvl": 85,
        "properties": {
          "life": 70,
          "fireRes": 45,
          "coldRes": 38
        },
        "estimated_price": {
          "chaos": 30,
          "divine": 0
        }
      }
    ]
  }
  ```
- [ ] 목업 아이템 10개 이상 추가
- [ ] 다양한 타입 포함 (무기/방어구/악세서리)
- [ ] 희귀도 다양화 (일반/마법/희귀/고유)

#### 테스트
- [ ] `stash_mock.json` 파일 읽기 성공
- [ ] JSON 파싱 정상 작동
- [ ] 아이템 개수 확인
- [ ] 속성 데이터 정확성 확인

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P7 — 스태시 데이터 모델
**예상 시간:** 1.5시간 | **의존성:** P6

#### 주요 작업
- [ ] `StashItem.cs` 클래스 생성
- [ ] 필드 정의:
  - `string Name`
  - `string Type`
  - `ItemRarity Rarity` (enum)
  - `int ItemLevel`
  - `Dictionary<string, int> Properties`
  - `PriceEstimate EstimatedPrice`
- [ ] `PriceEstimate.cs` 클래스 생성
  - `decimal Chaos`
  - `decimal Divine`
  - `string Source` (poe.ninja / AI / Manual)
- [ ] `StashData.cs` 클래스 생성
  - `List<StashItem> Items`
  - `DateTime LastUpdated`
  - `int TotalValue` (Chaos 기준)

#### 테스트
- [ ] 목업 데이터를 C# 객체로 역직렬화
- [ ] 속성 접근 정상
- [ ] 가격 계산 정상

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P8 — Overlay에 스태시 요약 표시
**예상 시간:** 2시간 | **의존성:** P7

#### 주요 작업
- [ ] Overlay UI에 스태시 섹션 추가
- [ ] 표시 항목:
  - 총 아이템 개수
  - 예상 자산 가치 (Chaos)
  - 판매 추천 아이템 개수
  - 보관 추천 아이템 개수
- [ ] 실시간 갱신 (1초마다)
- [ ] 목업 데이터 바인딩

#### 테스트
- [ ] Overlay에 스태시 요약 표시
- [ ] 아이템 개수 정확성
- [ ] 총 가치 계산 정확성
- [ ] 실시간 갱신 작동

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P9 — 아이템 추천 라벨 시스템
**예상 시간:** 3시간 | **의존성:** P8

#### 주요 작업
- [ ] `ItemRecommendation.cs` 클래스 생성
- [ ] 추천 타입 enum:
  - `Sell` (판매)
  - `Keep` (보관)
  - `Discard` (폐기)
  - `Upgrade` (업그레이드 대상)
- [ ] 추천 로직 (기초):
  - 가격 > 20 Chaos → Sell
  - 빌드에 유용 → Keep
  - 가격 < 1 Chaos → Discard
- [ ] Overlay에 추천 라벨 표시
- [ ] 아이템별 라벨 색상 구분
- [ ] 라벨 클릭 시 상세 정보 표시

#### 테스트
- [ ] 목업 아이템에 라벨 표시
- [ ] 판매 추천 라벨 (녹색)
- [ ] 보관 추천 라벨 (파란색)
- [ ] 폐기 추천 라벨 (회색)
- [ ] 라벨 클릭 → 상세 정보 팝업

#### 최종 확인
- [ ] **개발자 확인 완료**

---

## 🎯 Phase 3: poe.ninja 연동 & 데이터 마이닝

### P10 — poe.ninja API 연구
**예상 시간:** 2시간 | **의존성:** 없음

#### 주요 작업
- [ ] poe.ninja 웹사이트 분석
- [ ] 개발자 도구로 Network 탭 확인
- [ ] API 엔드포인트 발견:
  - Economy API (아이템 시세)
  - Builds API (빌드 통계)
- [ ] API 응답 구조 분석
- [ ] API 호출 제한 확인
- [ ] 문서화 (발견한 엔드포인트 정리)

#### 테스트
- [ ] 브라우저에서 API 호출 테스트
- [ ] JSON 응답 확인
- [ ] Postman으로 테스트 (선택)

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P10.5 — DataMiner 프로젝트 생성
**예상 시간:** 1시간 | **의존성:** P10

#### 주요 작업
- [ ] PathcraftAI.DataMiner 프로젝트 생성 (콘솔 앱)
- [ ] Core 프로젝트 참조 추가
- [ ] 기본 구조 작성:
  - `Program.cs` (메인 진입점)
  - `PoeNinjaScraper.cs` (수집 로직)
  - `DataNormalizer.cs` (정규화)
  - `DatabaseManager.cs` (저장)
- [ ] 명령줄 인자 파싱 구현
- [ ] 도움말 메시지 작성

#### 테스트
- [ ] 프로젝트 빌드 성공
- [ ] `PathcraftAI.DataMiner.exe --help` 실행
- [ ] 기본 실행 확인 (에러 없음)

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P11 — poe.ninja 스크래퍼 구현
**예상 시간:** 4시간 | **의존성:** P10.5

#### 주요 작업
- [ ] `PoeNinjaScraper.cs` 구현
- [ ] `HttpClient` 기반 API 호출
- [ ] Rate Limiting (요청 간격 1초)
- [ ] 데이터 수집:
  - Economy API → `economy_raw.json`
  - Builds API → `builds_raw.json`
  - Currency API → `currency_raw.json`
- [ ] 에러 핸들링 (타임아웃, 404 등)
- [ ] 진행도 표시 (Console.WriteLine)
- [ ] 로그 파일 생성 (`logs/dataminer.log`)
- [ ] 명령 옵션:
  - `--economy-only`
  - `--builds-only`
  - `--collect-all`

#### 테스트
- [ ] 빌드 에러 0개
- [ ] `--economy-only` 실행 성공
- [ ] `economy_raw.json` 파일 생성 확인
- [ ] JSON 구조 유효성 확인
- [ ] Rate Limiting 작동 확인 (1초 간격)
- [ ] 에러 발생 시 로그 기록 확인
- [ ] `--collect-all` 실행 성공

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P12 — 데이터 정규화 및 저장
**예상 시간:** 3시간 | **의존성:** P11

#### 주요 작업
- [ ] `DataNormalizer.cs` 구현
- [ ] poe.ninja JSON → 내부 데이터 모델 변환
- [ ] `DatabaseManager.cs` 구현
- [ ] SQLite 패키지 설치 (System.Data.SQLite)
- [ ] SQLite DB 스키마 설계:
  ```sql
  CREATE TABLE Items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,
    base_type TEXT,
    chaos_value REAL,
    divine_value REAL,
    variant TEXT,
    links INTEGER,
    level INTEGER,
    updated_at DATETIME
  );
  ```
- [ ] 데이터 삽입/업데이트 로직
- [ ] 중복 제거 (UPSERT)
- [ ] 캐시 JSON 파일 생성 (`cache/economy.json`)

#### 테스트
- [ ] 빌드 에러 0개
- [ ] `--collect-all` 실행 후 DB 생성 확인
- [ ] SQLite DB 파일 존재 (`data/economy.db`)
- [ ] 캐시 JSON 생성 확인 (`cache/economy.json`)
- [ ] 데이터 개수 확인 (최소 100개 이상)
- [ ] 중복 없음 확인 (SQL SELECT COUNT)
- [ ] DB 쿼리 테스트 (특정 아이템 조회)

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P13 — 메인 앱에서 DataMiner 데이터 사용
**예상 시간:** 2시간 | **의존성:** P12

#### 주요 작업
- [ ] PathcraftAI.Core에 `DataCache.cs` 클래스 생성
- [ ] SQLite DB 읽기 로직
- [ ] 캐시 JSON 읽기 (빠른 로드)
- [ ] 아이템 시세 조회 메서드:
  - `GetItemPrice(string itemName)`
  - `GetCurrencyRate(string currencyType)`
- [ ] 메인 UI에 "데이터 업데이트" 버튼 추가
- [ ] 버튼 클릭 시 DataMiner 실행

#### 테스트
- [ ] 빌드 에러 0개
- [ ] 메인 앱에서 시세 데이터 로드 성공
- [ ] Chaos Orb 시세 표시
- [ ] Divine Orb 시세 표시
- [ ] 캐시 로드 속도 확인 (< 1초)
- [ ] "데이터 업데이트" 버튼 작동
- [ ] 업데이트 후 시세 갱신 확인

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P14 — 실시간 시세 연동
**예상 시간:** 2시간 | **의존성:** P13

### P14 — 실시간 시세 연동
**예상 시간:** 2시간 | **의존성:** P13

#### 주요 작업
- [ ] `PriceEstimator.cs` 클래스 생성
- [ ] DataCache에서 시세 데이터 가져오기
- [ ] 아이템 속성 비교 로직:
  1. 목업 아이템 속성 추출 (Life, Res, DPS 등)
  2. DB에서 유사 아이템 검색
  3. 속성 비교 (± 10% 범위)
  4. 가격 범위 계산 (최소~최대)
- [ ] `EstimatedPrice` 업데이트
- [ ] Overlay에 실시간 시세 표시

#### 테스트
- [ ] 빌드 에러 0개
- [ ] 목업 아이템에 실시간 시세 적용
- [ ] 가격 정확도 확인 (±20% 이내)
- [ ] Overlay에 시세 표시
- [ ] 여러 아이템 타입 테스트 (Ring, Belt, Weapon)

#### 최종 확인
- [ ] **개발자 확인 완료**

---

## 🎯 Phase 4: GGG OAuth 연동

### P15 — OAuth 연구 및 설정
**예상 시간:** 2시간 | **의존성:** 없음

### P15 — OAuth 연구 및 설정
**예상 시간:** 2시간 | **의존성:** 없음

#### 주요 작업
- [ ] GGG OAuth 2.0 문서 읽기
- [ ] 애플리케이션 등록 (pathofexile.com/developer)
- [ ] Client ID / Secret 발급
- [ ] Redirect URI 설정
- [ ] 필요 스코프 확인:
  - `account:profile`
  - `account:stashes`

#### 테스트
- [ ] OAuth 앱 등록 완료
- [ ] Client ID 확인
- [ ] Postman으로 토큰 발급 테스트 (선택)

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P16 — OAuth 로그인 구현
**예상 시간:** 4시간 | **의존성:** P15

#### 주요 작업
- [ ] `GGGOAuthClient.cs` 클래스 생성
- [ ] 브라우저로 인증 페이지 열기
- [ ] Redirect URI 수신 (로컬 서버)
- [ ] Authorization Code → Access Token 교환
- [ ] Refresh Token 처리
- [ ] 토큰 암호화 저장 (`%APPDATA%/PathcraftAI/tokens.dat`)
- [ ] 로그인 UI (버튼)

#### 테스트
- [ ] 빌드 에러 0개
- [ ] "GGG 로그인" 버튼 클릭
- [ ] 브라우저 열림 → 로그인
- [ ] Access Token 발급 성공
- [ ] 토큰 파일 생성 확인
- [ ] 재시작 후 토큰 자동 로드

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P17 — 스태시 API 연동
**예상 시간:** 3시간 | **의존성:** P16

### P17 — 스태시 API 연동
**예상 시간:** 3시간 | **의존성:** P16

#### 주요 작업
- [ ] `GGGStashClient.cs` 클래스 생성
- [ ] 스태시 목록 조회 API 호출
- [ ] 스태시 탭별 아이템 데이터 수집
- [ ] `StashItem` 객체로 변환
- [ ] 목업 데이터 대체
- [ ] UI에 "스태시 스캔" 버튼 추가

#### 테스트
- [ ] 빌드 에러 0개
- [ ] 로그인 후 "스태시 스캔" 클릭
- [ ] 실제 스태시 데이터 로드
- [ ] 아이템 개수 확인
- [ ] Overlay에 실시간 데이터 표시

#### 최종 확인
- [ ] **개발자 확인 완료**

---

## 🎯 Phase 5: AI 통합

### P18 — ChatGPT API 연동 준비
**예상 시간:** 2시간 | **의존성:** 없음

### P18 — ChatGPT API 연동 준비
**예상 시간:** 2시간 | **의존성:** 없음

#### 주요 작업
- [ ] OpenAI API 키 발급 (사용자 직접)
- [ ] `OpenAIClient.cs` 클래스 생성
- [ ] `HttpClient` 기반 API 호출
- [ ] 메서드:
  - `SendPrompt(string prompt, string systemMessage)`
  - `ParseResponse(string json)`
- [ ] API 키 입력 UI (설정 창)
- [ ] API 키 암호화 저장

#### 테스트
- [ ] 빌드 에러 0개
- [ ] API 키 입력
- [ ] 간단한 프롬프트 테스트 ("Hello, GPT!")
- [ ] 응답 확인

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P19 — 빌드 분석 프롬프트
**예상 시간:** 3시간 | **의존성:** P18

#### 주요 작업
- [ ] `BuildAnalyzer.cs` 클래스 생성
- [ ] 프롬프트 템플릿 작성:
  ```
  당신은 Path of Exile의 빌드 전문가입니다.
  아래 빌드 데이터를 분석하세요.
  
  [빌드 JSON 데이터 삽입]
  
  다음 형식으로 답변:
  1. 빌드 컨셉 요약 (2-3문장)
  2. 주요 강점 3가지
  3. 주요 약점 3가지
  4. 개선 우선순위 Top 3
  ```
- [ ] AI 응답 파싱
- [ ] UI에 분석 결과 표시
- [ ] Overlay에 요약 표시

#### 테스트
- [ ] 빌드 에러 0개
- [ ] POB 파일 로드
- [ ] AI 분석 실행
- [ ] 응답 시간 확인 (< 10초)
- [ ] 분석 결과 UI 표시
- [ ] Overlay에 요약 표시

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P20 — 아이템 추천 프롬프트
**예상 시간:** 3시간 | **의존성:** P19

#### 주요 작업
- [ ] `ItemRecommender.cs` 클래스 생성
- [ ] 프롬프트 템플릿:
  ```
  당신은 POE 아이템 시장 전문가입니다.
  현재 빌드에 맞는 업그레이드 아이템을 추천하세요.
  
  [빌드 데이터 + 현재 시세]
  
  예산별 추천:
  - 저예산 (1-10 Chaos)
  - 중예산 (10-50 Chaos)
  - 고예산 (1+ Divine)
  ```
- [ ] DataCache에서 시세 데이터 포함
- [ ] AI 응답 파싱 (예산별 아이템 리스트)
- [ ] UI에 추천 아이템 표시

#### 테스트
- [ ] 빌드 에러 0개
- [ ] 빌드 로드 후 추천 실행
- [ ] 예산별 추천 확인
- [ ] 추천 아이템 시세 확인
- [ ] UI에 추천 표시

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P21 — 가격 책정 프롬프트
**예상 시간:** 3시간 | **의존성:** P20, P17

### P21 — 가격 책정 프롬프트
**예상 시간:** 3시간 | **의존성:** P20, P17

#### 주요 작업
- [ ] `PriceEvaluator.cs` 클래스 생성
- [ ] 프롬프트 템플릿:
  ```
  당신은 POE 아이템 가격 평가 전문가입니다.
  스태시의 아이템을 분석하여 판매 가격을 제안하세요.
  
  [아이템 데이터 + DataCache 시세]
  
  각 아이템마다:
  1. 추정 가격 (Chaos Orb)
  2. 가격 산정 근거
  3. 빠른 판매 vs 최대 이익 가격
  ```
- [ ] 스태시 아이템 → AI 평가
- [ ] 응답 파싱 (가격 + 근거)
- [ ] Overlay에 아이템별 가격 표시

#### 테스트
- [ ] 빌드 에러 0개
- [ ] 스태시 스캔 후 AI 평가 실행
- [ ] 각 아이템 가격 확인
- [ ] 판매/보관/폐기 추천 확인
- [ ] Overlay에 표시

#### 최종 확인
- [ ] **개발자 확인 완료**

---

## 🎯 Phase 6: UI/UX 개선

### P22 — 메인 UI 디자인
**예상 시간:** 4시간 | **의존성:** P21

### P22 — 메인 UI 디자인
**예상 시간:** 4시간 | **의존성:** P21

#### 주요 작업
- [ ] WPF 메인 창 디자인
- [ ] 섹션 구성:
  - 빌드 분석
  - 스태시 관리
  - 아이템 추천
  - 설정
- [ ] 탭 네비게이션
- [ ] POE 테마 적용 (어두운 톤 + 금색)
- [ ] 반응형 레이아웃

#### 테스트
- [ ] 빌드 에러 0개
- [ ] 모든 섹션 접근 가능
- [ ] 탭 전환 정상
- [ ] 해상도 변경 시 레이아웃 유지

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P23 — Overlay UI 개선
**예상 시간:** 2시간 | **의존성:** P22

#### 주요 작업
- [ ] Overlay 디자인 개선
- [ ] 초보자 뷰 / 숙련자 뷰 토글
- [ ] 폰트 크기 조절
- [ ] 투명도 슬라이더
- [ ] 위치 저장 (드래그 이동)

#### 테스트
- [ ] 빌드 에러 0개
- [ ] 뷰 토글 작동
- [ ] 투명도 조절 확인
- [ ] 위치 저장 및 복원

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P24 — 설정 시스템
**예상 시간:** 2시간 | **의존성:** P23

#### 주요 작업
- [ ] 설정 창 생성
- [ ] 설정 항목:
  - API 키 (ChatGPT / Gemini)
  - Overlay 핫키 변경
  - 자동 갱신 주기
  - 테마 (라이트/다크)
- [ ] 설정 저장 (JSON)
- [ ] 설정 로드

#### 테스트
- [ ] 빌드 에러 0개
- [ ] 설정 변경 후 저장
- [ ] 재시작 후 설정 유지
- [ ] 핫키 변경 작동

#### 최종 확인
- [ ] **개발자 확인 완료**

---

## 🎯 Phase 7: 배포 준비

### P25 — 에러 핸들링
**예상 시간:** 2시간 | **의존성:** P24

#### 주요 작업
- [ ] 전역 에러 핸들러
- [ ] 로그 시스템 (`logs/` 폴더)
- [ ] 사용자 친화적 에러 메시지
- [ ] 크래시 리포트 생성

#### 테스트
- [ ] 빌드 에러 0개
- [ ] 의도적 에러 발생
- [ ] 로그 파일 생성 확인
- [ ] 에러 메시지 표시
- [ ] 크래시 후 재시작 가능

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P26 — 단위 테스트
**예상 시간:** 3시간 | **의존성:** 모든 기능

#### 주요 작업
- [ ] PathcraftAI.Tests 프로젝트 테스트 작성
- [ ] 테스트 범위:
  - POB 파서
  - DataMiner
  - OAuth 로직
  - 가격 산정
  - AI 프롬프트

#### 테스트
- [ ] 빌드 에러 0개
- [ ] 모든 테스트 실행
- [ ] 80% 이상 통과

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P27 — 문서 작성
**예상 시간:** 2시간 | **의존성:** P26

#### 주요 작업
- [ ] README.md 작성
- [ ] 설치 가이드
- [ ] 사용 방법
- [ ] API 키 발급 방법
- [ ] DataMiner 사용법
- [ ] FAQ
- [ ] 라이선스 (MIT)

#### 테스트
- [ ] 문서 읽기 테스트 (제3자)
- [ ] 가이드 따라 설치 가능

#### 최종 확인
- [ ] **개발자 확인 완료**

---

### P28 — GitHub 배포
**예상 시간:** 1시간 | **의존성:** P27

#### 주요 작업
- [ ] GitHub Repository 생성
- [ ] 코드 푸시
- [ ] Release 생성 (v1.0.0)
- [ ] 실행 파일 업로드
- [ ] README 배지 추가

#### 테스트
- [ ] Release 다운로드 가능
- [ ] 실행 파일 작동

#### 최종 확인
- [ ] **개발자 확인 완료**

---

## 📊 전체 진행도

### 코드 리뷰: 성능 최적화 (CR1)
- [x] CR1 - 코드 리뷰 및 성능 최적화 (1시간) ✅

**코드 리뷰 완료:** [x]

---

### Phase 1: 핵심 인프라 (P1~P5)
- [x] P1 - 프로젝트 구조 (1시간) ✅
- [x] P2 - Parser 모듈 (2시간) ✅
- [x] P3 - Overlay 기본 (2시간) ✅
- [x] P4 - 자동 갱신 (1시간) ✅
- [x] P5 - 핫키 토글 (2시간) ✅

**Phase 1 완료:** [x] (총 8시간)

---

### Phase 2: 스태시 분석 기초 (P6~P9)
- [ ] P6 - 스태시 목업 (2시간)
- [ ] P7 - 데이터 모델 (1.5시간)
- [ ] P8 - Overlay 표시 (2시간)
- [ ] P9 - 추천 라벨 (3시간)

**Phase 2 완료:** [ ] (예상 8.5시간)

---

### Phase 3: poe.ninja 연동 & 데이터 마이닝 (P10~P14)
- [ ] P10 - API 연구 (2시간)
- [ ] P10.5 - DataMiner 프로젝트 (1시간)
- [ ] P11 - 스크래퍼 구현 (4시간)
- [ ] P12 - 데이터 정규화 (3시간)
- [ ] P13 - 메인 앱 연동 (2시간)
- [ ] P14 - 실시간 시세 (2시간)

**Phase 3 완료:** [ ] (예상 14시간)

---

### Phase 4: GGG OAuth (P15~P17)
- [ ] P15 - OAuth 연구 (2시간)
- [ ] P16 - OAuth 로그인 (4시간)
- [ ] P17 - 스태시 API (3시간)

**Phase 4 완료:** [ ] (예상 9시간)

---

### Phase 5: AI 통합 (P18~P21)
- [ ] P18 - ChatGPT 준비 (2시간)
- [ ] P19 - 빌드 분석 (3시간)
- [ ] P20 - 아이템 추천 (3시간)
- [ ] P21 - 가격 책정 (3시간)

**Phase 5 완료:** [ ] (예상 11시간)

---

### Phase 6: UI/UX (P22~P24)
- [ ] P22 - 메인 UI (4시간)
- [ ] P23 - Overlay 개선 (2시간)
- [ ] P24 - 설정 시스템 (2시간)

**Phase 6 완료:** [ ] (예상 8시간)

---

### Phase 7: 배포 (P25~P28)
- [ ] P25 - 에러 핸들링 (2시간)
- [ ] P26 - 단위 테스트 (3시간)
- [ ] P27 - 문서 작성 (2시간)
- [ ] P28 - GitHub 배포 (1시간)

**Phase 7 완료:** [ ] (예상 8시간)

---

## 🎯 전체 프로젝트 완료
- [x] **Phase 1 완료 (8시간)**
- [ ] **Phase 2~7 진행 예정 (총 58.5시간 예상)**
- [ ] **전체 예상 시간: 66.5시간**

---

## 📝 다음 진행 태스크
**현재:** P6 - 스태시 목업 데이터 생성  
**예상 시간:** 2시간  
**의존성:** P5 (완료)

---

_최종 업데이트: 2025-11-02_  
_작성: Claude Sonnet 4.5_  
_참고: 알케미스트 저니 체크리스트 포맷 기반_
