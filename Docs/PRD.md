# PathcraftAI - Product Requirements Document (PRD)

**Version:** 2.0
**Last Updated:** 2025-11-15
**Status:** In Development

---

## 1. Product Overview

### 1.1 Vision
Path of Exile 플레이어를 위한 **AI 기반 올인원 빌드 도우미**

### 1.2 Mission
- 초보자도 쉽게 빌드를 찾고 이해할 수 있게
- AI로 빌드 분석 및 개선 방안 제시
- 무료로도 충분히 유용하고, AI 기능은 선택적

### 1.3 Target Users
- **초보자**: 빌드 찾기 어려운 신규 유저
- **중급자**: 빌드 최적화 원하는 유저
- **고급자**: 여러 빌드 비교/분석 필요한 유저

---

## 2. Core Features

### 2.1 무료 기능 (Tier 1)

#### 2.1.1 빌드 검색
- **YouTube 빌드 검색**
  - 키워드 검색 (예: "Death's Oath", "Elementalist")
  - 리그 버전 필터 (3.27, 3.26 등)
  - 조회수/좋아요 순 정렬

- **POB 링크 자동 추출**
  - YouTube 설명란에서 pobb.in, pastebin.com 링크 추출
  - 클릭 한 번에 Path of Building 실행

- **아이템 가격 정보**
  - poe.ninja API 연동
  - 빌드 필수 아이템 가격 표시
  - 예산 예측 ("시작: 50c, 완성: 20div")

#### 2.1.2 빌드 관리
- 북마크 기능
- 빌드 노트 작성
- 로컬 저장 (서버 없음)

#### 2.1.3 광고
- 앱 하단 배너 광고
- 검색 결과 사이 광고 (침해적이지 않게)

---

### 2.2 AI 기능 (API 키 필요)

#### 2.2.1 지원 AI 모델
사용자가 **본인의 API 키**를 입력하여 사용:

1. **OpenAI GPT-4o**
   - 발급: https://platform.openai.com/api-keys
   - 비용: ~$0.01 / 분석

2. **Google Gemini**
   - 발급: https://makersuite.google.com/
   - 비용: 무료 (일일 제한)

3. **Anthropic Claude Sonnet**
   - 발급: https://console.anthropic.com/
   - 비용: ~$0.02 / 분석

#### 2.2.2 AI 분석 기능

**A. 빌드 추천**
- 입력: "Death's Oath 초보용 추천해줘"
- 출력:
  - 빌드 개요 (플레이스타일, 난이도)
  - 장점/단점 (3-4개씩)
  - 추천 대상 (예산, 경험)
  - 핵심 시너지 (아이템/스킬 조합)

**B. 단계별 로드맵**
- 레벨링 가이드 (1-70 스킬 순서)
- 예산별 업그레이드
  - 시작: 20c
  - 중간: 10div
  - 완성: 100div
- 각 단계별 필수 아이템

**C. 빌드 디버거** (프리미엄 기능)
- POB 파일 업로드
- AI가 문제점 찾기
  - 저항 부족
  - 생명력/ES 부족
  - DPS 낮은 이유
- 구체적 해결 방법 제시
  - "이 아이템을 OO로 교체"
  - "패시브 트리에서 XX 추가"

---

### 2.3 프리미엄 기능 (Tier 2)

#### 2.3.1 광고 제거

**옵션 A: 월 구독**
- 가격: $2.99 / 월
- 혜택:
  - 모든 광고 제거
  - 우선 지원
  - 프리미엄 배지

**옵션 B: 후원 (POE Overlay 스타일)**
- Patreon / Ko-fi 연동
- 티어:
  - $3: 광고 제거 1개월
  - $10: 광고 제거 + 특별 배지
  - $25: 영구 광고 제거

#### 2.3.2 추가 기능 (나중에)
- 빌드 비교 (최대 3개 동시)
- 메타 트렌드 분석
- Discord 알림 (새 빌드 업데이트)

---

## 3. Technical Architecture

### 3.1 기술 스택

#### Frontend (C# Desktop App)
- **Framework**: WPF (Windows Presentation Foundation)
- **Language**: C# .NET 8
- **UI Library**: ModernWpf (Modern UI)

#### Backend (Python)
- **Language**: Python 3.12
- **APIs**:
  - YouTube Data API v3
  - OpenAI API
  - Anthropic Claude API
  - Google Gemini API
  - poe.ninja API
  - POE Official API

#### Data Storage
- **Local**: SQLite (빌드 북마크, 설정)
- **Cache**: JSON files (검색 결과 캐시)

### 3.2 시스템 아키텍처

```
┌─────────────────────────────────────┐
│   PathcraftAI.exe (C# WPF)         │
│   - UI 렌더링                       │
│   - 광고 SDK                        │
│   - 설정 관리                       │
└──────────────┬──────────────────────┘
               │ Process.Start()
               ▼
┌─────────────────────────────────────┐
│   Python Backend (.venv)           │
│   - youtube_build_collector.py     │
│   - pob_parser.py                  │
│   - ai_build_analyzer.py           │
│   - poe_ninja_fetcher.py           │
└──────────────┬──────────────────────┘
               │ API Calls
               ▼
┌─────────────────────────────────────┐
│   External APIs                     │
│   - YouTube                         │
│   - OpenAI/Claude/Gemini            │
│   - poe.ninja                       │
└─────────────────────────────────────┘
```

### 3.3 데이터 흐름

1. **빌드 검색**
   ```
   사용자 입력 → C# UI → Python 백엔드 → YouTube API
                                         → POB 파싱
                                         → poe.ninja API
                        ← JSON 결과 ←
   C# UI에 표시
   ```

2. **AI 분석**
   ```
   POB 링크 입력 → Python → POB 파싱 → 빌드 데이터
                          → AI API (사용자 키) → 분석 결과
                  ← JSON ←
   C# UI에 표시
   ```

---

## 4. User Experience (UX)

### 4.1 메인 화면

```
┌────────────────────────────────────────────────┐
│ PathcraftAI                    [설정] [후원]  │
├────────────────────────────────────────────────┤
│                                                │
│  🔍 [검색창: "빌드 이름 입력..."]              │
│                                                │
│  리그: [3.27 ▼]  정렬: [조회수 ▼]             │
│                                                │
├────────────────────────────────────────────────┤
│  검색 결과:                                    │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │ [썸네일] Death's Oath Occultist          │ │
│  │          - GhazzyTV                      │ │
│  │          조회수: 45K | 좋아요: 1.8K       │ │
│  │          POB: https://pobb.in/...        │ │
│  │          예상 비용: 20div                │ │
│  │          [🔖 북마크] [🤖 AI 분석]        │ │
│  └──────────────────────────────────────────┘ │
│                                                │
├────────────────────────────────────────────────┤
│ [광고 배너] (프리미엄: 광고 제거)              │
└────────────────────────────────────────────────┘
```

### 4.2 AI 분석 화면

```
┌────────────────────────────────────────────────┐
│ AI 빌드 분석 - Death's Oath Occultist         │
├────────────────────────────────────────────────┤
│                                                │
│  AI 모델: [GPT-4o ▼]  [API 키 설정 →]        │
│                                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                                │
│  📋 빌드 개요                                  │
│  Caustic Arrow + Death Aura 카오스 빌드       │
│  지속 피해 중심, 안전한 플레이스타일           │
│                                                │
│  ✅ 장점                                       │
│  • 넓은 범위 커버                              │
│  • 안정적 생존력                               │
│  • 다양한 컨텐츠 클리어                        │
│                                                │
│  ❌ 단점                                       │
│  • 단일 타겟 DPS 부족                          │
│  • 초기 장비 투자 필요                         │
│                                                │
│  💡 핵심 시너지                                │
│  • Impresence → Malevolence 무료 예약         │
│  • Viridi's Veil → 원소 면역                  │
│                                                │
│  [📥 전체 가이드 다운로드]                     │
│                                                │
└────────────────────────────────────────────────┘
```

### 4.3 설정 화면

```
┌────────────────────────────────────────────────┐
│ 설정                                           │
├────────────────────────────────────────────────┤
│                                                │
│  🔑 AI API 키 설정                             │
│                                                │
│  OpenAI (GPT)                                  │
│  [sk-proj-...                    ] [발급 방법] │
│  예상 비용: $0.01 / 분석                       │
│                                                │
│  Google Gemini                                 │
│  [                               ] [발급 방법] │
│  무료 (일일 제한)                              │
│                                                │
│  Anthropic Claude                              │
│  [                               ] [발급 방법] │
│  예상 비용: $0.02 / 분석                       │
│                                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                                │
│  💎 프리미엄                                    │
│  [광고 제거 - $2.99/월]  [후원하기]           │
│                                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                                │
│  ⚙️ 일반                                       │
│  리그 버전: [3.27 ▼]                           │
│  테마: [다크 ▼]                                │
│  언어: [한국어 ▼]                              │
│                                                │
└────────────────────────────────────────────────┘
```

---

## 5. Business Model

### 5.1 수익원

1. **광고 수익**
   - Google AdSense
   - 예상: 1000 사용자 → 월 $50-100

2. **프리미엄 구독**
   - 월 $2.99
   - 목표: 100 구독자 → 월 $300

3. **후원 (Patreon/Ko-fi)**
   - 자발적 후원
   - 목표: 50 후원자 → 월 $150-300

### 5.2 성장 목표

| 기간 | 사용자 | 구독자 | 예상 수익 |
|------|--------|--------|-----------|
| 3개월 | 1,000 | 20 | $150/월 |
| 6개월 | 5,000 | 100 | $500/월 |
| 1년 | 20,000 | 300 | $1,500/월 |

### 5.3 경쟁 우위

vs 기존 서비스:
- **poebuilds.cc**: 빌드 모음 → 우리: AI 분석 + 디버거
- **POE Overlay**: 게임 오버레이 → 우리: 빌드 추천
- **Path of Building**: 계산기 → 우리: 초보자 가이드

---

## 6. Development Roadmap

### Phase 1: MVP (4주)
- [x] Python 백엔드 완성
  - [x] YouTube 검색
  - [x] POB 파싱
  - [x] AI 분석 (OpenAI/Claude)
  - [x] poe.ninja 연동
- [ ] C# 앱 기본 UI
  - [ ] 검색 화면
  - [ ] 결과 표시
  - [ ] Python 백엔드 호출
- [ ] 무료 기능 구현
  - [ ] 빌드 검색
  - [ ] POB 링크 표시
  - [ ] 북마크

### Phase 2: AI 기능 (2주)
- [ ] API 키 설정 UI
- [ ] AI 분석 화면
- [ ] 3개 AI 모델 통합

### Phase 3: 수익화 (2주)
- [ ] 광고 SDK 통합
- [ ] 프리미엄 구독 시스템
- [ ] 후원 링크 연동

### Phase 4: 고급 기능 (4주)
- [ ] 빌드 디버거
- [ ] 단계별 로드맵 생성
- [ ] 메타 분석

---

## 7. Success Metrics

### 7.1 핵심 지표 (KPI)

1. **사용자 지표**
   - DAU (Daily Active Users): 500+
   - MAU (Monthly Active Users): 5,000+
   - 재방문율: 40%+

2. **수익 지표**
   - 광고 수익: $200+/월
   - 구독 전환율: 2%
   - 평균 수익: $500+/월

3. **사용 지표**
   - 평균 검색 횟수: 5회/사용자
   - AI 분석 사용: 30%
   - 북마크 수: 평균 3개/사용자

### 7.2 성공 기준

**3개월 목표:**
- ✅ 1,000+ 다운로드
- ✅ 50+ 프리미엄 사용자
- ✅ 월 $150+ 수익

**6개월 목표:**
- ✅ 10,000+ 다운로드
- ✅ 200+ 프리미엄 사용자
- ✅ 월 $500+ 수익
- ✅ Reddit r/PathOfExileBuilds 추천

**1년 목표:**
- ✅ 50,000+ 다운로드
- ✅ 500+ 프리미엄 사용자
- ✅ 월 $2,000+ 수익
- ✅ GGG 공식 인정 (팬 사이트 등록)

---

## 8. Legal & Compliance

### 8.1 API 사용 정책

✅ **안전:**
- YouTube API: 정식 사용
- poe.ninja API: 공개 API
- POE Official API: 정식 사용
- POB: MIT License

✅ **사용자 API 키 모델:**
- 사용자가 본인 키 입력
- 재판매 없음 → 법적 문제 없음

### 8.2 상표권

- ❌ POE 로고 무단 사용 금지
- ✅ "비공식 팬 도구" 명시
- ✅ "Path of Exile™ is a trademark of Grinding Gear Games" 표기

### 8.3 개인정보 보호

- ✅ API 키 로컬 저장 (암호화)
- ✅ 서버에 개인정보 미전송
- ✅ GDPR 준수 (유럽 사용자)

---

## 9. Support & Community

### 9.1 사용자 지원

- GitHub Issues: 버그 리포트
- Discord 서버: 커뮤니티 지원
- 이메일: pathcraftai@gmail.com (예시)

### 9.2 문서

- 사용 가이드
- API 키 발급 튜토리얼
- 빌드 검색 팁
- 자주 묻는 질문 (FAQ)

---

## 10. Appendix

### 10.1 참고 자료

- POE Official API: https://www.pathofexile.com/developer/docs
- YouTube API: https://developers.google.com/youtube
- poe.ninja: https://poe.ninja
- POE Overlay (벤치마크): https://github.com/Kyusung4698/PoE-Overlay

### 10.2 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0 | 2025-11-14 | 초기 작성 |
| 2.0 | 2025-11-15 | 비즈니스 모델 재정의 (API 키 모델) |

---

**문서 승인:**
- Product Owner: [이름]
- Tech Lead: [이름]
- Date: 2025-11-15
