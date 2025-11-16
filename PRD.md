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

### 3.2 Core Features (3-Tier Hybrid Model)

#### Feature 1: YouTube 빌드 검색 (P0) - All Tiers
**설명:** YouTube에서 빌드 영상 검색, POB 링크 자동 추출
**사용자 가치:** 10배 빠른 검색 (< 5초)
**티어:** Free, Premium, Expert (모두 무제한)
**우선순위:** P0 (Must) ✅ 완료

#### Feature 2: poe.ninja 아이템 가격 (P0) - All Tiers
**설명:** 실시간 아이템 시세 조회 (33,610개)
**사용자 가치:** 사기 방지, 예산 계획
**티어:** Free, Premium, Expert (모두 무제한)
**우선순위:** P0 (Must) ✅ 완료

#### Feature 3: AI 빌드 가이드 (P0) - Hybrid Model ✨ NEW
**설명:** 3-Tier 하이브리드 AI 분석 시스템

**Free Tier:**
- POB 기반 AI 요약 (3-4줄, GPT-4o-mini)
  - 빌드 타입 (메인 스킬, 무기)
  - 리그 스타터 적합도 (100% 정확!)
  - 예산, 난이도
- 본인 API 키로 전체 분석 가능:
  - **Google Gemini (무료!)** - 60 requests/day
  - OpenAI GPT-4 - ~$0.03/analysis
  - Anthropic Claude - ~$0.02/analysis
- **광고 없음**

**Premium Tier ($2/month):**
- Free 기능 +
- **월 20회 AI 전체 분석 크레딧**
- PathcraftAI의 GPT-4 API 사용
- API 키 발급 불필요
- 매월 1일 크레딧 리셋
- 우선 이메일 지원

**Expert Tier ($5/month):**
- Premium 기능 +
- **Fine-tuned POE Expert AI 무제한**
  - 모델: ft:gpt-3.5-turbo:pathcraftai:poe-expert-v1
  - 10,000+ POE Q&A 학습
  - 메타 분석, 빌드 최적화 전문
- GGG OAuth 빌드 분석 (무제한)
- 빌드 디버거 (고급)
- Expert Discord 채널

**사용자 가치:**
- Free: 무료로도 충분히 유용 (AI 맛보기)
- Premium: 편의성 (API 키 불필요, $2/월)
- Expert: 전문가급 분석 (Fine-tuned, $5/월)

**우선순위:** P0 (Must) ✅ 완료

#### Feature 4: POB 파싱 정확도 (P0) - All Tiers ✨ NEW
**설명:** POB XML 실제 데이터 기반 정확한 분석
**기능:**
- 메인 스킬 자동 추출 (추측 금지)
- 아이템 레벨 요구사항 분석
- 리그 스타터 자동 판단 (max_item_level < 50)
- AI 응답 검증 레이어

**사용자 가치:**
- 초보자 오해 방지
- 100% 정확한 리그 스타터 판단
- 신뢰도 향상

**우선순위:** P0 (Must) ✅ 완료

#### Feature 5: C# WPF 데스크톱 앱 (P1)
**설명:** Windows 네이티브 앱
**사용자 가치:** 편리한 UI, 빠른 성능
**우선순위:** P1 (Should) 📋 계획

#### Feature 6: GGG OAuth 캐릭터 분석 (P1) - Premium/Expert
**설명:** GGG 공식 승인 OAuth 2.1 통합 (2025-06-07 승인)
**사용자 가치:**
- 본인 빌드 자동 분석
- 개인화 추천
- 스태쉬 탭 연동

**티어:**
- Premium: 5회/월
- Expert: 무제한

**우선순위:** P1 (Should) ✅ 완료 (OAuth 승인)

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

### 7.1 Tier Structure (Hybrid 3-Tier Model)

| Feature | Free | Premium ($2/월) | Expert ($5/월) |
|---------|------|-----------------|----------------|
| **빌드 검색** |
| YouTube 검색 | ✅ Unlimited | ✅ Unlimited | ✅ Unlimited |
| POB 링크 추출 | ✅ Unlimited | ✅ Unlimited | ✅ Unlimited |
| poe.ninja 가격 | ✅ Unlimited | ✅ Unlimited | ✅ Unlimited |
| **AI 분석** |
| AI 요약 (짧게) | ✅ POB 기반 | ✅ POB 기반 | ✅ POB 기반 |
| AI 전체 분석 | User API Keys* | 20회/월** | Unlimited*** |
| AI 모델 | Gemini/GPT-4/Claude | GPT-4 | Fine-tuned POE Expert |
| **고급 기능** |
| OAuth 빌드 분석 | ❌ | ✅ (5개/월) | ✅ (무제한) |
| 빌드 디버거 | ❌ | ❌ | ✅ |
| **지원** |
| 광고 | 없음 | 없음 | 없음 |
| 우선 지원 | ❌ | ⚠️ (이메일) | ✅ (Discord) |
| 베타 기능 | ❌ | ❌ | ✅ Early Access |

**Free Tier 상세:**
- *User API Keys: 본인 Gemini (무료!), OpenAI, Claude API 키 사용
- Gemini 추천: 60 requests/day, $0 cost
- AI 요약: GPT-4o-mini 기반, 무제한

**Premium Tier 상세:**
- **월 20회 AI 전체 분석 크레딧 포함
- PathcraftAI의 GPT-4 API 사용 (API 키 불필요)
- 매월 1일 크레딧 리셋
- 비용/분석: ~$0.03

**Expert Tier 상세:**
- ***Fine-tuned POE Expert AI 무제한
- 모델: ft:gpt-3.5-turbo:pathcraftai:poe-expert-v1
- 10,000+ POE Q&A 학습
- 비용/분석: ~$0.0045

### 7.2 Pricing

**Monthly:**
- Free: $0
- Premium: $2/월
- Expert: $5/월

**Annual (17% discount):**
- Premium: $20/년 (vs $24)
- Expert: $50/년 (vs $60)

### 7.3 Revenue Model

**Payment Methods:**
- Patreon (월간/연간)
- Ko-fi (후원)
- Stripe (자체 결제, 향후)

### 7.4 Cost Analysis (MAU 1,000) - Hybrid 3-Tier Model

**Revenue (보수적 시나리오):**
- Free Tier (850명): **$25/월** (광고, 현실적)
  - AI 요약만 사용: 850명 × 5회/월 = 4,250회
  - 광고 없음 (전략적 선택)
- Premium (100명 × $2, 10% 전환): **$200/월**
- Expert (50명 × $5, 5% 전환): **$250/월**
- Ko-fi 후원 (30명, 3% × $5 평균): **$150/월**
- **Total Revenue: $625/월**

**Costs:**
- LLM API: **$88/월**
  - Free AI 요약: 850명 × 5회/월 × $0.005 (GPT-4o-mini) = $21.25
  - Premium: 100명 × 20회 × $0.03 (GPT-4) = $60.00
  - Expert: 50명 × 30회 × $0.0045 (Fine-tuned) = $6.75
- Hosting: $0 (Desktop app)
- Payment Processing: $25 (5% of $500 subscription)
- **Total Costs: $113/월**

**Profit: $512/월 (78% margin)**

**초기 투자:**
- Fine-tuning: $129 (1회)
- 회수 기간: <1개월

**낙관적 시나리오 (MAU 5,000, 6개월 후):**
- Premium (500명 × $2): $1,000/월
- Expert (250명 × $5): $1,250/월
- Ko-fi (150명 × $5): $750/월
- **Revenue: $3,000/월**
- **Costs: $334/월**
- **Profit: $2,666/월 (연 $32,000)**

**전환율 개선 효과 (AI 요약 맛보기):**
- 맛보기 없음: Premium 전환율 7%
- 맛보기 있음: Premium 전환율 15% (+8%p)
- 추가 수익: $160/월
- AI 요약 비용: $21/월
- **순이익 증가: $139/월 (투자 대비 7배 ROI)**

### 7.5 Competitive Analysis

| 제품 | 가격 | 주요 기능 | PathcraftAI 차별화 |
|------|------|-----------|-------------------|
| **POE Overlay** | Premium (비공개) | 인게임 가격 체크 | **AI 빌드 가이드** |
| **Xiletrade** | 무료 | 가격 체크만 | **Fine-tuned LLM** |
| **POE Vault** | 무료 (광고) | 수동 큐레이션 | **자동화 + 최신** |
| **PathcraftAI** | **$0/$2/$5** | 통합 솔루션 | **OAuth + AI 분석** |

**Pricing Strategy:**
- Free $0: **광고 없음** - 무료로도 충분히 유용
- Premium $2: POE Overlay 대비 **투명하고 저렴** - API 키 불필요
- Expert $5: Fine-tuned LLM 독점 기능 - POE 전문가급 분석
- Annual 17% 할인: 장기 고객 확보

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
