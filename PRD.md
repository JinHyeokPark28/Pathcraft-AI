# PathcraftAI - Product Requirements Document (PRD)

**Version:** 2.0
**Last Updated:** 2025-11-16
**Status:** In Development
**Target Release:** Q1 2026
**Owner:** Shovel
**Target Users:** Path of Exile 플레이어 (한국 커뮤니티 중심)

---

## 1. Executive Summary

### 1.1 What (무엇을)
PathcraftAI는 Path of Exile 플레이어를 위한 AI 기반 빌드 검색 및 분석 도구입니다.

### 1.2 Why (왜)
POE 플레이어들은:
- 빌드 찾기 어려움 (YouTube, Reddit, 포럼 분산)
- 빌드 분석 어려움 (저항, DPS 계산 복잡)
- 최신 메타 파악 어려움 (패치마다 변경)

### 1.3 Who (누구를 위해)
- **초보자:** 리그 스타터 빌드 찾기
- **중급자:** 메타 빌드 빠르게 찾기
- **고급자:** 빌드 최적화 원함

### 1.4 Success Metrics
- MAU 1,000+ (3개월 내)
- 유료 전환율 5%+ (Supporter + Expert)
- 월 순이익 $600+

---

## 2. Problem Statement

### 2.1 Current Situation
- YouTube: 검색 느림, POB 링크 수동 추출
- poe.ninja: 가격만, 빌드 가이드 없음
- Reddit: 검증된 빌드 적음
- POE 공식 사이트: Ladder API 느림 (100초+)

### 2.2 Pain Points
1. 정보 분산 (여러 소스 수동 검색)
2. POB 링크 추출 번거로움
3. 빌드 분석 직접 해야 함
4. 최신 패치 반영 안 됨

### 2.3 Jobs to be Done
- When 새 리그 시작할 때, I want to 리그 스타터 빌드 찾기, so I can 빠르게 레벨링
- When 빌드가 약할 때, I want to 문제점 파악, so I can 개선 가능
- When 아이템 살 때, I want to 가격 확인, so I can 사기 안 당함

---

## 3. Solution

### 3.1 Product Vision
PathcraftAI는 POE 플레이어를 위한 원스톱 빌드 솔루션입니다.

### 3.2 Core Features

#### Feature 1: YouTube 빌드 검색 (P0)
**설명:** YouTube에서 빌드 영상 검색, POB 링크 자동 추출
**사용자 가치:** 10배 빠른 검색 (< 5초)
**우선순위:** P0 (Must) ✅ 완료

#### Feature 2: poe.ninja 아이템 가격 (P0)
**설명:** 실시간 아이템 시세 조회 (33,610개)
**사용자 가치:** 사기 방지, 예산 계획
**우선순위:** P0 (Must) ✅ 완료

#### Feature 3: AI 빌드 가이드 생성 (P0)
**설명:** LLM 기반 종합 빌드 가이드
**사용자 가치:** 초보자도 이해 가능한 가이드
**우선순위:** P0 (Must) ✅ 완료

#### Feature 4: Fine-tuned POE Expert LLM (P1)
**설명:** POE 전문가급 Fine-tuned GPT-3.5
**사용자 가치:** 메타 분석, 최적화 조언
**우선순위:** P1 (Should) 🔄 진행 중

#### Feature 5: C# WPF 데스크톱 앱 (P1)
**설명:** Windows 네이티브 앱
**사용자 가치:** 편리한 UI, 빠른 성능
**우선순위:** P1 (Should) 📋 계획

#### Feature 6: POB 파일 업로드 (P2)
**설명:** 로컬 POB 파일 분석
**사용자 가치:** pobb.in 없이도 분석
**우선순위:** P2 (Nice-to-have) 📋 백로그

### 3.3 Out of Scope
- ❌ 모바일 앱 (PC 게임)
- ❌ 웹 버전 (데스크톱 우선)
- ❌ 커뮤니티 기능 (댓글, 평점)
- ❌ 인게임 오버레이 (기술적 난이도 높음)

---

## 4. User Personas

### Persona 1: 초보 플레이어 "민수" (Primary)
- **나이:** 25세
- **경험:** POE 시작 1개월
- **니즈:**
  1. 리그 스타터 빌드
  2. 레벨링 가이드
  3. 예산 빌드 (< 100 chaos)
- **페인 포인트:**
  1. 정보 너무 많음
  2. 전문 용어 모름
  3. 빌드 선택 어려움
- **사용 시나리오:**
  1. 새 리그 시작 → "Death's Oath" 검색
  2. YouTube 영상 3개 발견 → POB 링크 자동 추출
  3. AI 가이드 읽고 → 빌드 시작

### Persona 2: 고급 플레이어 "철수" (Secondary)
- **나이:** 32세
- **경험:** POE 5년차
- **니즈:**
  1. 빌드 최적화
  2. 메타 분석
  3. 고급 팁
- **사용 시나리오:**
  1. Expert Tier 구독
  2. Fine-tuned LLM으로 빌드 분석
  3. 최적화 조언 받음

---

## 5. Technical Architecture

### 5.1 Tech Stack

**Backend:**
- Python 3.12: 빌드 검색, 분석 로직
- YouTube Data API v3
- poe.ninja API
- OpenAI API (GPT-4, Fine-tuned GPT-3.5)
- Anthropic API (Claude-3)

**Frontend (계획):**
- C# WPF (.NET 8): Windows 네이티브
- ModernWpf: 다크/라이트 테마

**Deployment:**
- Desktop: Windows 10+ (64-bit)
- Python: Embedded (사용자 설치 불필요)

### 5.2 System Diagram
```
[사용자 입력: "Death's Oath"]
         ↓
[C# WPF UI] (계획)
         ↓
[Python Backend]
    ├── YouTube 검색
    ├── Reddit 검색
    ├── poe.ninja 가격
    └── LLM 가이드 생성
         ↓
[결과 표시]
```

---

## 6. Success Metrics

### 6.1 Launch Metrics (3개월)

**User Acquisition:**
- MAU: 1,000+
- DAU: 200+
- Retention (D7): 30%+

**Engagement:**
- 평균 세션: 5분+
- 검색 횟수: 3회/세션

**Revenue:**
- 광고 수익: $300/월
- Supporter: $250/월 (50명 × $5)
- Expert: $150/월 (10명 × $15)
- **Total: $700/월**

### 6.2 Product KPIs
- 검색 속도: < 5초
- LLM 가이드 생성: < 30초
- 앱 크래시율: < 1%

---

## 7. Pricing & Monetization

### 7.1 Tier Structure

| Feature | Free | Supporter ($5/월) | Expert ($15/월) |
|---------|------|-------------------|-----------------|
| YouTube 검색 | ✅ | ✅ | ✅ |
| POB 링크 추출 | ✅ | ✅ | ✅ |
| 가격 정보 | ✅ | ✅ | ✅ |
| AI 가이드 | Mock | GPT-4/Claude (5회) | Fine-tuned (무제한) |
| 광고 | 있음 | 없음 | 없음 |

### 7.2 Revenue Model
- 광고: Google AdSense
- Supporter: Patreon / Ko-fi
- Expert: 자체 결제 (Stripe)

### 7.3 Cost Analysis (MAU 1,000)

**Revenue:**
- Free Tier (900명): $300/월 (광고)
- Supporter (50명 × $5): $250/월
- Expert (10명 × $15): $150/월
- **Total Revenue: $700/월**

**Costs:**
- LLM API (Fine-tuned): $8.40/월
  - Supporter: 50명 × 5회 × $0.03 = $7.50
  - Expert: 10명 × 20회 × $0.0045 = $0.90
- Hosting: $0 (Desktop app)
- Payment Processing: $35 (5%)
- **Total Costs: $43.40/월**

**Profit: $656.60/월 (93% margin)**

---

## 8. Milestones & Timeline

### Phase 7: Fine-tuned LLM (2025-11-16 ~ 2025-11-30)
- [x] Phase 7.1: Fallback 로직 (2025-11-16)
- [ ] Phase 7.2: 데이터 수집 (2025-11-23)
- [ ] Phase 7.3: Fine-tuning (2025-11-24)
- [ ] Phase 7.4: Expert Tier 베타 (2025-11-30)

### Phase 8: C# WPF UI (2025-12-01 ~ 2025-12-14)
- [ ] .NET 8 프로젝트 생성
- [ ] Python 백엔드 연동
- [ ] Tier 선택 UI
- [ ] Windows 배포

### Phase 9: MVP 출시 (2025-12-15)
- [ ] 베타 테스터 모집 (50명)
- [ ] 피드백 수집
- [ ] 버그 수정

### Phase 10: 정식 출시 (2026-01-01)
- [ ] Reddit r/pathofexile 공개
- [ ] YouTube 크리에이터 협업
- [ ] MAU 1,000 달성

---

## 9. Risks & Mitigations

### Risk 1: Fine-tuning 품질 낮음
- **Probability:** Medium
- **Impact:** High (Expert Tier 이탈)
- **Mitigation:**
  - 데이터 품질 검수 (10,000+ Q&A)
  - GPT-4 Fallback 유지
  - 베타 테스터 피드백
  - 환불 정책 명시

### Risk 2: 사용자 적음
- **Probability:** Medium
- **Impact:** Medium (수익 부족)
- **Mitigation:**
  - Reddit 마케팅
  - YouTube 크리에이터 후원
  - 무료 Tier 제공 (진입 장벽 낮춤)
  - 한국 커뮤니티 우선

### Risk 3: API 비용 초과
- **Probability:** Low
- **Impact:** High (운영 중단)
- **Mitigation:**
  - Query Limit (Supporter 5회/월)
  - 캐싱 시스템 (YouTube 결과 24시간)
  - 월 예산 Alert
  - Mock Fallback 항상 유지

### Risk 4: OpenAI API 장애
- **Probability:** Low
- **Impact:** Medium (Expert Tier 불만)
- **Mitigation:**
  - Smart Fallback: Fine-tuned → GPT-4 → Mock
  - 에러 메시지 명확히 표시
  - Status page 제공

---

## 10. Competitive Analysis

### 10.1 Competitors

| Product | Strengths | Weaknesses | Differentiation |
|---------|-----------|------------|-----------------|
| **POE Ninja** | 실시간 가격, 메타 통계 | 빌드 가이드 없음 | 우리: AI 가이드 제공 |
| **POB** | 정확한 계산 | 빌드 찾기 어려움 | 우리: YouTube 검색 |
| **POE Vault** | 수동 큐레이션 | 업데이트 느림 | 우리: 자동화, 최신 |
| **YouTube 검색** | 영상 많음 | POB 링크 수동 추출 | 우리: 자동 추출 |

### 10.2 Unique Value Proposition
"POE 빌드 검색부터 AI 분석까지, 단 10초 안에."

---

## 11. Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-16 | 2.0 | Fine-tuned LLM 추가, Tier 구조 확정, 수익 분석 | Shovel |
| 2025-11-01 | 1.0 | Initial PRD | Shovel |

---

## Appendix A: User Stories

### Epic 1: 빌드 검색
- **US-001:** As a 초보 플레이어, I want to "Death's Oath" 검색, so I can 빌드 영상 찾기
- **US-002:** As a 중급자, I want to POB 링크 자동 추출, so I can 빠르게 빌드 가져오기
- **US-003:** As a 고급자, I want to 최신 패치 필터, so I can 메타 빌드만 보기

### Epic 2: AI 분석
- **US-004:** As a 초보자, I want to AI 가이드 읽기, so I can 빌드 이해하기
- **US-005:** As a Expert 유저, I want to Fine-tuned 분석, so I can 최적화 조언
- **US-006:** As a Supporter 유저, I want to GPT-4/Claude 선택, so I can 선호 모델 사용

### Epic 3: 가격 확인
- **US-007:** As a 모든 유저, I want to 아이템 가격 보기, so I can 예산 계획
- **US-008:** As a 모든 유저, I want to Divine/Chaos 환산, so I can 비교하기

---

**Document Owner:** Shovel
**Next Review:** 2025-12-01 (Phase 8 시작 전)
**GitHub:** https://github.com/JinHyeokPark28/Pathcraft-AI
