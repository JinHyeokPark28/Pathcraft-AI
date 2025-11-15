# PathcraftAI - Task Checklist

**Last Updated:** 2025-11-15
**Current Sprint:** Phase 1 - MVP Development

---

## ✅ Completed Tasks

### Python Backend

- [x] **YouTube API 통합** (2025-11-15)
  - [x] YouTube Data API v3 클라이언트 구현
  - [x] POB 링크 추출 (pobb.in, pastebin.com)
  - [x] Mock 모드 지원
  - [x] 파일: `youtube_build_collector.py`

- [x] **POB 파싱** (2025-11-15)
  - [x] pobb.in XML 다운로드 및 디코딩
  - [x] 빌드 데이터 추출 (클래스, 스킬, 아이템)
  - [x] 젬 링크 파싱
  - [x] 장비 정보 파싱
  - [x] 파일: `pob_parser.py`

- [x] **AI 빌드 분석** (2025-11-15)
  - [x] OpenAI GPT-4o 통합
  - [x] Claude Sonnet 통합 (코드 완성)
  - [x] 한글 인코딩 문제 해결
  - [x] 빌드 분석 프롬프트 작성
  - [x] 파일: `ai_build_analyzer.py`

- [x] **통합 검색 시스템** (2025-11-15)
  - [x] YouTube + POB 통합
  - [x] JSON 저장 기능
  - [x] 파일: `youtube_pob_search.py`

- [x] **poe.ninja 데이터 수집** (2025-11-15)
  - [x] 33,610개 아이템 수집
  - [x] 이미지 다운로드
  - [x] 파일: `poe_ninja_fetcher.py`

- [x] **개발 환경 설정**
  - [x] Python venv 생성
  - [x] requirements.txt 작성
  - [x] .gitignore 설정
  - [x] .env 파일 설정

- [x] **Git 저장소 설정** (2025-11-15)
  - [x] GitHub 리포지토리 연결
  - [x] 초기 커밋 (757 files)
  - [x] Remote: https://github.com/JinHyeokPark28/Pathcraft-AI

- [x] **문서 작성**
  - [x] PRD.md (Product Requirements Document)
  - [x] README.md
  - [x] YOUTUBE_API_SETUP.md
  - [x] SYSTEM_STATUS.md

---

## 🔄 In Progress

### Phase 1: MVP Development (Week 1-4)

#### C# Desktop App Setup
- [ ] **프로젝트 초기화**
  - [ ] WPF 프로젝트 생성 (.NET 8)
  - [ ] NuGet 패키지 설치
    - [ ] ModernWpf (Modern UI)
    - [ ] Newtonsoft.Json (JSON 파싱)
  - [ ] 프로젝트 구조 설정

#### UI 기본 틀
- [ ] **메인 윈도우**
  - [ ] XAML 레이아웃 작성
  - [ ] 상단 메뉴바 (설정, 후원)
  - [ ] 검색창 UI
  - [ ] 결과 표시 영역
  - [ ] 하단 광고 배너 영역 (placeholder)

- [ ] **스타일 & 테마**
  - [ ] 다크 모드 테마
  - [ ] 라이트 모드 테마
  - [ ] POE 스타일 디자인 (색상, 폰트)

#### Python 백엔드 연동
- [ ] **Process 호출**
  - [ ] C#에서 Python 프로세스 실행
  - [ ] JSON 결과 파싱
  - [ ] 에러 핸들링
  - [ ] 로딩 인디케이터

- [ ] **빌드 검색 기능**
  - [ ] 검색 버튼 클릭 → Python 호출
  - [ ] YouTube 결과 표시
  - [ ] POB 링크 버튼
  - [ ] 조회수/좋아요 표시

---

## 📋 Planned Tasks

### Phase 1: MVP (Remaining)

#### 무료 기능
- [ ] **poe.ninja 가격 표시**
  - [ ] 아이템 가격 API 호출
  - [ ] UI에 가격 정보 표시
  - [ ] "예산 예상" 계산

- [ ] **빌드 북마크**
  - [ ] SQLite 데이터베이스 설정
  - [ ] 북마크 추가/삭제 기능
  - [ ] 북마크 목록 UI
  - [ ] 로컬 저장

- [ ] **검색 필터**
  - [ ] 리그 버전 선택 (3.27, 3.26)
  - [ ] 정렬 (조회수, 좋아요, 최신)
  - [ ] 클래스 필터

---

### Phase 2: AI 기능 (Week 5-6)

#### API 키 설정
- [ ] **설정 화면**
  - [ ] API 키 입력 UI (GPT/Gemini/Claude)
  - [ ] 키 검증 기능
  - [ ] 로컬 암호화 저장
  - [ ] "발급 방법" 가이드 링크

- [ ] **Gemini API 통합**
  - [ ] Google Gemini 클라이언트 구현
  - [ ] Python 코드 작성
  - [ ] C# 연동

#### AI 분석 화면
- [ ] **분석 결과 UI**
  - [ ] 빌드 개요 섹션
  - [ ] 장점/단점 리스트
  - [ ] 추천 대상 표시
  - [ ] 핵심 시너지 하이라이트

- [ ] **AI 모델 선택**
  - [ ] 드롭다운 (GPT/Gemini/Claude)
  - [ ] 각 모델별 설정
  - [ ] 비용 예상 표시

---

### Phase 3: 수익화 (Week 7-8)

#### 광고 통합
- [ ] **Google AdSense 설정**
  - [ ] AdSense 계정 생성
  - [ ] C# 광고 SDK 통합
  - [ ] 배너 광고 테스트
  - [ ] 광고 정책 준수

#### 프리미엄 기능
- [ ] **구독 시스템**
  - [ ] 결제 게이트웨이 연동 (Stripe/PayPal)
  - [ ] 구독 상태 관리
  - [ ] 광고 제거 로직
  - [ ] 프리미엄 배지

- [ ] **후원 연동**
  - [ ] Patreon 링크
  - [ ] Ko-fi 링크
  - [ ] 후원자 명단 표시

---

### Phase 4: 고급 기능 (Week 9-12)

#### 빌드 디버거
- [ ] **POB 업로드**
  - [ ] 파일 선택 UI
  - [ ] POB 파일 파싱
  - [ ] AI에게 빌드 데이터 전송

- [ ] **문제점 분석**
  - [ ] 저항 부족 감지
  - [ ] 생명력/ES 부족 감지
  - [ ] DPS 분석
  - [ ] 구체적 해결 방법 제시

#### 단계별 로드맵
- [ ] **레벨링 가이드**
  - [ ] 1-70 스킬 순서 생성
  - [ ] 각 레벨별 권장 아이템
  - [ ] AI 기반 자동 생성

- [ ] **예산별 업그레이드**
  - [ ] 시작 (20c) → 중간 (10div) → 완성 (100div)
  - [ ] 각 단계별 필수 아이템
  - [ ] 우선순위 표시

---

## 🐛 Known Issues

### High Priority
- [ ] YouTube API 키 환경변수 로딩 문제 (dotenv)
  - 임시 해결: export로 직접 설정
  - 영구 해결: .env 파일 로딩 로직 수정

### Medium Priority
- [ ] pobapi 0.5.0 stats API 호환성 문제
  - 현재: fallback 모드 사용
  - 해결: pobapi 0.6+ 대기 or 대안 구현

### Low Priority
- [ ] Windows 콘솔 한글 인코딩 (해결됨 - UTF-8 강제)

---

## 📊 Progress Tracking

### Sprint 1 (Week 1-2): Backend Complete ✅
- [x] YouTube API 통합
- [x] POB 파싱
- [x] AI 분석
- [x] poe.ninja 데이터 수집
- [x] Git 설정
- [x] 문서 작성

### Sprint 2 (Week 3-4): C# MVP
- [ ] WPF 프로젝트 설정
- [ ] 기본 UI 구현
- [ ] Python 백엔드 연동
- [ ] 무료 기능 (검색, 북마크)

### Sprint 3 (Week 5-6): AI Features
- [ ] API 키 설정 UI
- [ ] AI 분석 화면
- [ ] 3개 AI 모델 통합

### Sprint 4 (Week 7-8): Monetization
- [ ] 광고 SDK
- [ ] 구독 시스템
- [ ] 후원 연동

### Sprint 5 (Week 9-12): Advanced Features
- [ ] 빌드 디버거
- [ ] 단계별 로드맵
- [ ] 메타 분석

---

## 🎯 Milestones

### M1: Python Backend Complete ✅ (2025-11-15)
- All Python modules working
- AI analysis tested
- Data collection complete

### M2: MVP Release (Target: 2025-12-15)
- C# app working
- Free features complete
- Python integration stable

### M3: AI Features (Target: 2026-01-01)
- 3 AI models integrated
- API key management
- Premium features ready

### M4: Public Beta (Target: 2026-01-15)
- Ads integrated
- Subscription system
- Community feedback

### M5: v1.0 Release (Target: 2026-02-01)
- All features complete
- Build debugger working
- Documentation complete

---

## 📝 Notes

### Development Environment
- Python: 3.12
- C#: .NET 8
- IDE: Visual Studio 2022
- Git: GitHub

### API Keys Required
- ✅ YouTube Data API v3
- ✅ OpenAI API
- ⏳ Anthropic Claude API (optional)
- ⏳ Google Gemini API (optional)

### Dependencies
- Python: anthropic, openai, google-api-python-client, requests, beautifulsoup4, python-dotenv
- C#: ModernWpf, Newtonsoft.Json

---

**Next Action:** C# WPF 프로젝트 초기화 및 기본 UI 구현 시작
