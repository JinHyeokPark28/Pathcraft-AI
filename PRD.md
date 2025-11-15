# PathcraftAI - Product Requirements Document (PRD)

**Version:** 1.0
**Last Updated:** 2025-11-15
**Status:** Pre-Development
**Target Release:** Q1 2026

---

## 1. Product Overview

### 1.1 Vision
PathcraftAI는 Path of Exile 플레이어들이 빌드를 쉽고 빠르게 찾고, AI 기반 분석을 통해 더 나은 선택을 할 수 있도록 돕는 **올인원 빌드 검색 및 분석 도구**입니다.

### 1.2 Mission
- YouTube, poe.ninja 등 다양한 소스에서 빌드를 통합 검색
- AI(GPT/Gemini/Claude)를 활용한 빌드 분석 및 추천
- 무료 사용자와 프리미엄 사용자 모두에게 가치 제공
- 광고 및 후원 기반 지속 가능한 운영 모델

### 1.3 Target Users

#### Primary Users
- **POE 초보자** (30%): 어떤 빌드를 시작해야 할지 모르는 플레이어
- **중급 플레이어** (50%): 메타 빌드를 빠르게 찾고 싶은 플레이어
- **고급 플레이어** (20%): 빌드 최적화 및 디버깅을 원하는 플레이어

#### User Personas

**페르소나 1: 초보 플레이어 "민수"**
- 나이: 25세
- 경험: POE 시작한 지 1개월
- 니즈: 리그 스타터 빌드, 레벨링 가이드, 예산 빌드
- 페인 포인트: 정보가 너무 많고 어디서 시작해야 할지 모름

**페르소나 2: 중급 플레이어 "지영"**
- 나이: 30세
- 경험: 5개 리그 플레이
- 니즈: 메타 빌드 빠른 검색, 가격 정보, 유튜브 가이드
- 페인 포인트: poe.ninja는 가격만, poebuilds.cc는 느리고 오래됨

**페르소나 3: 고급 플레이어 "준호"**
- 나이: 28세
- 경험: 10+ 리그, 빌드 제작 경험
- 니즈: POB 빌드 디버깅, AI 최적화 제안
- 페인 포인트: 저항/DPS 계산 직접 해야 함, 문제 찾기 어려움

---

## 2. Core Features

### 2.1 2-Tier System (간소화)

#### Tier 1: Free (무료 - 광고 포함)
**타겟:** 모든 사용자

**기능:**
- ✅ YouTube 빌드 검색 (poe 버전 + 키워드)
- ✅ poe.ninja 아이템 가격 표시
- ✅ POB 링크 다운로드
- ✅ 빌드 북마크 (로컬 저장)
- ✅ 검색 필터 (클래스, 리그, 정렬)
- ✅ **AI 빌드 분석** (사용자 API 키 입력 시)
  - GPT-4o / Gemini 1.5 Pro / Claude 3.5 Sonnet 지원
  - 빌드 개요, 장점/단점, 추천 대상, 핵심 시너지
  - AI 모델 선택 (드롭다운)
  - 분석 결과 저장 (로컬)
- ⚠️ **광고 표시** (하단 배너)

**법적 안전성:**
- ✅ 사용자가 직접 API 키 발급 → 재판매 아님
- ✅ OpenAI/Google/Anthropic 개인 약관 준수
- ✅ GDPR 준수 (로컬 저장만)

**경쟁력:**
- poebuilds.cc보다 빠름 (YouTube API)
- poe.ninja보다 직관적 (영상 + 가격 통합)
- **AI 분석까지 무료** (API 키만 있으면)

**사용 예시:**
```
1. 검색창에 "Death's Oath" 입력
2. YouTube 영상 3개 + POB 링크 4개 표시
3. 아이템 가격: Death's Oath = 1.00 divine
4. [설정]에서 OpenAI API 키 입력 (1회만)
5. [AI 분석] 버튼 → GPT-4o가 빌드 분석 (2-3초)
6. 결과: 빌드 개요, 장점/단점, 추천 대상
```

#### Tier 2: Premium (프리미엄 - 광고 제거)
**타겟:** 광고 없는 깔끔한 경험을 원하는 사용자

**기능:**
- ✅ **광고 제거** (깔끔한 UI)
- ✅ 모든 무료 기능 포함
  - YouTube 검색, poe.ninja 가격
  - AI 빌드 분석 (사용자 API 키)
  - 빌드 북마크
- ✅ 프리미엄 배지
- ✅ 우선 지원 (GitHub Issues)
- ✅ **3일 무료 체험** (광고 없이 사용)

**가격:**
- 구독: $2.99/월 (Stripe/PayPal)
- 후원: Patreon/Ko-fi (1회성 또는 정기)

**수익 모델:**
- 광고 수익: $200-500/월 (예상, DAU 500+ 기준)
- 구독 수익: $150/월 (50명 × $2.99)
- 후원 수익: $50-100/월

**전환 전략:**
- 3일 무료 체험 → 광고 없는 경험
- 광고가 성가신 사용자 → 프리미엄 구독
- 월 $2.99 = 커피 한 잔 가격

**경쟁사 비교:**
| 기능 | PathcraftAI | POE Overlay | poebuilds.cc |
|------|-------------|-------------|--------------|
| 무료 검색 | ✅ | ✅ | ✅ |
| AI 분석 | ✅ (무료, 사용자 API) | ❌ | ❌ |
| 광고 | 무료: ⚠️ / 유료: ✅ 제거 | 무료 | 무료 |
| 가격 정보 | ✅ | ✅ | ❌ |
| 속도 | ⚡ 빠름 | ⚡ 빠름 | 🐌 느림 |
| 프리미엄 가격 | $2.99/월 | 무료 | 무료 |

---

### 2.2 Feature Details

#### 2.2.1 YouTube 빌드 검색
**구현:**
- YouTube Data API v3
- 검색 쿼리: `poe {version} {keyword} build guide`
- 메타데이터: 제목, 채널, 조회수, 좋아요, 날짜
- POB 링크 자동 추출 (regex: pobb.in, pastebin.com)

**UI:**
```
┌─────────────────────────────────────────────┐
│ 검색: [Death's Oath        ] [🔍 검색]     │
├─────────────────────────────────────────────┤
│ 📺 YouTube 결과 (3)                         │
│                                              │
│ 1. [POE 3.27] Death's Oath Occultist       │
│    채널: GhazzyTV | 조회수: 45,230         │
│    [POB 다운로드] [영상 보기]              │
│                                              │
│ 2. Budget Death's Oath Guide               │
│    채널: Zizaran | 조회수: 28,500          │
│    [POB 다운로드] [영상 보기] [AI 분석]   │
└─────────────────────────────────────────────┘
```

#### 2.2.2 AI 빌드 분석
**지원 모델:**
- OpenAI GPT-4o (추천)
- Google Gemini 1.5 Pro
- Anthropic Claude 3.5 Sonnet

**분석 항목:**
1. **Build Overview** (2-3문장)
   - 빌드 컨셉
   - 플레이스타일

2. **Strengths** (3-4개)
   - 매핑 속도
   - 보스 DPS
   - 생존력

3. **Weaknesses** (3-4개)
   - 장비 의존도
   - 레벨링 난이도

4. **Recommended For** (2문장)
   - 타겟 플레이어
   - 예산 레벨 (리그 스타터 / 중간 / 고예산)

5. **Key Synergies** (2-3개)
   - 아이템 + 젬 상호작용
   - 패시브 트리 최적화

**프롬프트 예시:**
```python
prompt = f"""You are a Path of Exile build expert. Analyze:

**Build:** {build_name}
**Class:** {class_name} / {ascendancy}
**Main Skill:** {main_skill}
**Key Items:** {items}

Provide analysis in Korean (한국어) with:
1. Build Overview (빌드 개요)
2. Strengths (장점)
3. Weaknesses (단점)
4. Recommended For (추천 대상)
5. Key Synergies (핵심 시너지)
"""
```

#### 2.2.3 빌드 북마크
**데이터베이스:** SQLite (로컬)

**스키마:**
```sql
CREATE TABLE bookmarks (
    id INTEGER PRIMARY KEY,
    build_name TEXT NOT NULL,
    pob_link TEXT,
    youtube_url TEXT,
    class TEXT,
    ascendancy TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);
```

**UI:**
```
┌─────────────────────────────────────────────┐
│ 📚 내 북마크 (5)                           │
│                                              │
│ 1. ⭐ Death's Oath Occultist               │
│    POB: pobb.in/abc123                     │
│    메모: "리그 스타터 후보"                │
│    [수정] [삭제]                           │
│                                              │
│ 2. ⭐ Mageblood TS Deadeye                 │
│    POB: pobb.in/def456                     │
│    [수정] [삭제]                           │
└─────────────────────────────────────────────┘
```

#### 2.2.4 poe.ninja 가격 통합
**API:** poe.ninja Economy API

**표시 정보:**
- Divine Orb 가격
- Chaos Orb 가격
- 아이템별 가격 (divines / chaos)
- 가격 변동 (↑↓)

**예산 계산:**
```python
def calculate_build_cost(gear_list):
    total_chaos = 0
    for item in gear_list:
        price = get_poeninja_price(item['name'])
        total_chaos += price

    total_divine = total_chaos / get_divine_price()

    return {
        'chaos': total_chaos,
        'divine': total_divine,
        'budget_tier': get_budget_tier(total_divine)
    }

# 예산 티어
# < 10 div: 리그 스타터
# 10-50 div: 중간 예산
# > 50 div: 고예산
```

---

## 3. Technical Architecture

### 3.1 System Architecture

```
┌─────────────────────────────────────────────────┐
│              C# WPF Desktop App                  │
│  ┌─────────────┐  ┌────────────┐  ┌──────────┐ │
│  │ Main Window │  │ Settings   │  │ Bookmark │ │
│  │ (Search)    │  │ (API Keys) │  │ Manager  │ │
│  └─────────────┘  └────────────┘  └──────────┘ │
└─────────────────────────────────────────────────┘
                      ↓ Process.Start()
┌─────────────────────────────────────────────────┐
│           Python Backend (CLI Scripts)          │
│  ┌──────────────────┐  ┌──────────────────┐    │
│  │ youtube_pob_     │  │ ai_build_        │    │
│  │ search.py        │  │ analyzer.py      │    │
│  └──────────────────┘  └──────────────────┘    │
│  ┌──────────────────┐  ┌──────────────────┐    │
│  │ pob_parser.py    │  │ poe_ninja_       │    │
│  │                  │  │ fetcher.py       │    │
│  └──────────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────┘
                      ↓ JSON Output
┌─────────────────────────────────────────────────┐
│              External APIs                       │
│  ┌──────────────┐  ┌──────────┐  ┌──────────┐  │
│  │ YouTube      │  │ poe.ninja│  │ AI APIs  │  │
│  │ Data API v3  │  │ API      │  │ (3종)    │  │
│  └──────────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────┘
```

### 3.2 Technology Stack

#### Frontend (C# WPF)
- **.NET 8.0**: 최신 LTS 버전
- **ModernWpf**: 모던 UI 테마
- **Newtonsoft.Json**: JSON 파싱
- **SQLite**: 로컬 데이터베이스

#### Backend (Python)
- **Python 3.12**: 최신 안정 버전
- **google-api-python-client**: YouTube API
- **anthropic**: Claude API
- **openai**: GPT API
- **requests**: HTTP 클라이언트
- **beautifulsoup4**: HTML 파싱
- **python-dotenv**: 환경변수 관리

#### APIs
- **YouTube Data API v3**: 무료 할당량 10,000 units/day
- **poe.ninja API**: 무료, 제한 없음
- **OpenAI API**: 사용자 API 키
- **Google Gemini API**: 사용자 API 키
- **Anthropic Claude API**: 사용자 API 키

### 3.3 Data Flow

**1. 빌드 검색 플로우**
```
사용자 입력 (C#)
  → Process.Start("python youtube_pob_search.py --keyword 'Death's Oath'")
  → Python: YouTube 검색 + POB 링크 추출
  → JSON 출력
  → C#: JSON 파싱 → UI 표시
```

**2. AI 분석 플로우**
```
POB 링크 클릭 (C#)
  → Process.Start("python ai_build_analyzer.py --pob-url '...' --provider openai")
  → Python: POB 파싱 → AI 분석
  → JSON 출력 (분석 결과 + 토큰 사용량)
  → C#: 결과 표시
```

**3. 북마크 저장 플로우**
```
북마크 버튼 (C#)
  → SQLite INSERT
  → 로컬 DB 저장
  → 북마크 목록 갱신
```

### 3.4 API Key Management

**저장 위치:**
- Windows: `%APPDATA%\PathcraftAI\api_keys.encrypted`
- 암호화: AES-256 (User's Windows Password + Machine GUID)

**보안 고려사항:**
- ✅ 로컬 암호화 저장
- ✅ HTTPS만 사용
- ✅ API 키 절대 로그 출력 금지
- ✅ .gitignore에 api_keys.* 추가

**API 키 검증:**
```python
def validate_openai_key(api_key):
    try:
        client = OpenAI(api_key=api_key)
        client.models.list()
        return True
    except:
        return False
```

---

## 4. User Experience

### 4.1 Main Window (검색 화면)

```
┌──────────────────────────────────────────────────────────┐
│ PathcraftAI                        ⚙️ 설정   💰 후원    │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  🔍 빌드 검색                                            │
│  ┌────────────────────────────────────┐  [🔎 검색]      │
│  │ Death's Oath                       │                  │
│  └────────────────────────────────────┘                  │
│                                                           │
│  리그: [3.27 ▼]  클래스: [전체 ▼]  정렬: [조회수 ▼]   │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 📺 YouTube 결과 (3)                                      │
│                                                           │
│  1. [POE 3.27] Death's Oath Occultist Budget Starter    │
│     채널: GhazzyTV | 👁️ 45,230 | 👍 1,823             │
│     POB: pobb.in/abc123                                  │
│     [📥 다운로드] [▶️ 영상] [🤖 AI 분석] [⭐ 북마크]   │
│                                                           │
│  2. League Starter Death's Oath Guide                   │
│     채널: Zizaran | 👁️ 28,500 | 👍 987                │
│     POB: pobb.in/def456                                  │
│     [📥 다운로드] [▶️ 영상] [🤖 AI 분석] [⭐ 북마크]   │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 💰 아이템 가격 (poe.ninja)                               │
│                                                           │
│  Death's Oath: 1.00 divine (112.8 chaos) ↑ +5%         │
│  Viridi's Veil: 0.50 divine (56.4 chaos) → 0%          │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 📊 [광고 배너 영역 - Google AdSense]                    │
└──────────────────────────────────────────────────────────┘
```

### 4.2 AI Analysis Window (분석 화면)

```
┌──────────────────────────────────────────────────────────┐
│ 🤖 AI 빌드 분석                              [닫기 ✕]   │
├──────────────────────────────────────────────────────────┤
│ 빌드: Death's Oath Occultist                            │
│ AI 모델: [GPT-4o ▼]                    분석 시간: 2.3s │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 📝 빌드 개요                                             │
│                                                           │
│ Caustic Arrow와 Death Aura를 활용한 카오스 지속 피해   │
│ 빌드입니다. Occultist의 카오스 특화 패시브를 통해      │
│ 매핑 속도가 빠르고 생존력이 뛰어납니다.                │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ ✅ 장점                                                  │
│                                                           │
│ • 빠른 매핑 속도 (Death Aura 자동 피해)                │
│ • 높은 생존력 (ES + Chaos Resistance)                  │
│ • 저예산 리그 스타터 가능 (< 10 divine)                │
│ • 조작 간편 (이동만으로 적 처치)                       │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ ❌ 단점                                                  │
│                                                           │
│ • 보스 DPS 낮음 (지속 피해 특성)                       │
│ • Death's Oath 구매 필수 (1 divine)                    │
│ • 레벨링 초반 약함 (Death's Oath 62레벨부터)          │
│ • 물리 피해 방어력 부족                                 │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 🎯 추천 대상                                             │
│                                                           │
│ 카오스 빌드를 선호하고 매핑 중심 플레이를 즐기는       │
│ 플레이어에게 추천합니다. 예산: 중간 (10-20 divine)    │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 🔗 핵심 시너지                                           │
│                                                           │
│ • Death's Oath + Increased Area = 넓은 Death Aura      │
│ • Viridi's Veil + CI = 원소 상태 이상 면역             │
│ • Occultist Profane Bloom = 폭발 체인                  │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 💡 토큰 사용: 450 in / 620 out (약 $0.02)              │
│                                                           │
│ [💾 저장] [📋 복사] [🔄 다시 분석]                      │
└──────────────────────────────────────────────────────────┘
```

### 4.3 Settings Window (설정 화면)

```
┌──────────────────────────────────────────────────────────┐
│ ⚙️ 설정                                      [저장] [✕] │
├──────────────────────────────────────────────────────────┤
│ 🔑 API 키 설정                                           │
│                                                           │
│ OpenAI (GPT)                                             │
│ ┌────────────────────────────────────────┐  [테스트]    │
│ │ sk-proj-...                            │              │
│ └────────────────────────────────────────┘              │
│ 💡 발급 방법: https://platform.openai.com/api-keys     │
│                                                           │
│ Google Gemini                                            │
│ ┌────────────────────────────────────────┐  [테스트]    │
│ │                                        │              │
│ └────────────────────────────────────────┘              │
│ 💡 발급 방법: https://aistudio.google.com/apikey       │
│                                                           │
│ Anthropic Claude                                         │
│ ┌────────────────────────────────────────┐  [테스트]    │
│ │                                        │              │
│ └────────────────────────────────────────┘              │
│ 💡 발급 방법: https://console.anthropic.com/keys        │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 🎨 UI 설정                                               │
│                                                           │
│ 테마: ⚫ 다크 모드  ⚪ 라이트 모드                      │
│ 언어: [한국어 ▼]                                        │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ 💰 프리미엄                                              │
│                                                           │
│ 현재 상태: 무료 (광고 표시)                            │
│                                                           │
│ [🌟 프리미엄 구독 ($2.99/월)]  [❤️ 후원하기]          │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 4.4 Bookmark Manager (북마크 관리)

```
┌──────────────────────────────────────────────────────────┐
│ 📚 내 북마크                                  [닫기 ✕]  │
├──────────────────────────────────────────────────────────┤
│ 총 5개 빌드                                              │
│                                                           │
│ ┌────────────────────────────────────────────────────┐  │
│ │ ⭐ Death's Oath Occultist                         │  │
│ │ POB: pobb.in/abc123                                │  │
│ │ 메모: "리그 스타터 1순위"                          │  │
│ │ 추가일: 2025-11-15                                 │  │
│ │ [수정] [삭제] [POB 열기] [AI 분석]               │  │
│ └────────────────────────────────────────────────────┘  │
│                                                           │
│ ┌────────────────────────────────────────────────────┐  │
│ │ ⭐ Mageblood TS Deadeye                           │  │
│ │ POB: pobb.in/def456                                │  │
│ │ 메모: "고예산 목표 빌드"                           │  │
│ │ 추가일: 2025-11-14                                 │  │
│ │ [수정] [삭제] [POB 열기] [AI 분석]               │  │
│ └────────────────────────────────────────────────────┘  │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 5. Business Model & Monetization

### 5.1 Revenue Streams

#### 1. Ad Revenue (광고 수익)
- **Platform:** Google AdSense
- **Ad Type:** Banner ads (하단 고정)
- **Estimated:** $200-500/month (DAU 500 기준)

**Calculation:**
```
DAU: 500 users
Ad impressions per user: 10 sessions/day
Total impressions: 5,000/day
CPM (Cost per 1000 impressions): $2-4
Daily revenue: $10-20
Monthly revenue: $300-600
```

#### 2. Premium Subscription (구독)
- **Price:** $2.99/month
- **Features:** Ad removal + priority support
- **Estimated:** $150/month (50 subscribers)

**Conversion Funnel:**
```
MAU: 5,000 users
→ DAU: 500 users (10% engagement)
→ Trial users: 100 users (20% try AI)
→ Paying users: 50 users (10% conversion)
→ Revenue: 50 × $2.99 = $149.50/month
```

#### 3. Donations (후원)
- **Platforms:** Patreon, Ko-fi
- **Estimated:** $50-100/month

**Donor Tiers:**
- $1/month: Supporter badge
- $5/month: Early access to features
- $10/month: Name in credits

### 5.2 Cost Structure

**Fixed Costs:**
- Server hosting: $0 (desktop app, no backend server)
- Domain: $12/year (~$1/month)
- GitHub: $0 (public repo)

**Variable Costs:**
- Google AdSense: $0 (free)
- Payment processing: 3% of subscription revenue (~$4.50/month)

**Total Monthly Cost:** ~$5

**Net Profit:**
- Best case: $600 (ads) + $150 (subs) + $100 (donations) - $5 = **$845/month**
- Average case: $400 + $100 + $50 - $5 = **$545/month**
- Worst case: $200 + $50 + $20 - $5 = **$265/month**

### 5.3 Legal & Compliance

#### API Key Model (사용자 제공)
✅ **Legally Safe**
- 사용자가 직접 API 키 발급
- PathcraftAI는 중개만 (reselling ❌)
- OpenAI/Google/Anthropic 개인 약관 준수

#### Data Privacy
✅ **GDPR Compliant**
- 모든 데이터 로컬 저장 (서버 없음)
- API 키 암호화 저장
- 사용자 데이터 수집 안 함

#### POE Data Usage
✅ **Allowed**
- poe.ninja API: Public, 무료
- YouTube API: Google 약관 준수
- POE Official API: 공개 Ladder 데이터

#### Ad Policies
✅ **Google AdSense Policy**
- 성인 콘텐츠 없음
- 게임 관련 앱 허용
- 클릭 유도 금지

---

## 6. Development Roadmap

### Phase 1: MVP (Week 1-4)
**Goal:** 무료 기능 완성

**Tasks:**
- [x] Python backend (YouTube + POB + AI)
- [ ] C# WPF 프로젝트 초기화
- [ ] 메인 윈도우 UI (검색 화면)
- [ ] Python 프로세스 호출 (Process.Start)
- [ ] JSON 결과 파싱 및 표시
- [ ] 북마크 기능 (SQLite)
- [ ] poe.ninja 가격 표시

**Deliverables:**
- 빌드 검색 가능
- POB 링크 다운로드
- 북마크 저장/관리

### Phase 2: AI Features (Week 5-6)
**Goal:** AI 분석 기능 추가

**Tasks:**
- [ ] API 키 설정 UI
- [ ] API 키 암호화 저장
- [ ] AI 분석 윈도우 UI
- [ ] AI 모델 선택 (GPT/Gemini/Claude)
- [ ] 분석 결과 표시
- [ ] 토큰 사용량 표시
- [ ] 3일 무료 체험 로직

**Deliverables:**
- AI 빌드 분석 가능
- 3개 AI 모델 지원

### Phase 3: Monetization (Week 7-8)
**Goal:** 수익화 시스템 구축

**Tasks:**
- [ ] Google AdSense SDK 통합
- [ ] 배너 광고 표시
- [ ] Stripe/PayPal 결제 연동
- [ ] 구독 상태 관리
- [ ] 광고 제거 로직
- [ ] Patreon/Ko-fi 링크 추가

**Deliverables:**
- 광고 표시
- 프리미엄 구독 가능
- 후원 링크 활성화

### Phase 4: Advanced Features (Week 9-12)
**Goal:** 고급 기능 추가

**Tasks:**
- [ ] POB 파일 업로드 (빌드 디버거)
- [ ] AI 빌드 디버깅 (저항/DPS 분석)
- [ ] 레벨링 가이드 생성
- [ ] 예산별 업그레이드 경로
- [ ] 메타 분석 (인기 빌드 Top 10)
- [ ] 한국어/영어 다국어 지원

**Deliverables:**
- 빌드 디버거 완성
- 레벨링 가이드
- 다국어 지원

---

## 7. Success Metrics

### 7.1 Launch Metrics (1개월)

**User Acquisition:**
- MAU (Monthly Active Users): 1,000+
- DAU (Daily Active Users): 100+
- Retention Rate (D7): 30%+

**Engagement:**
- Average sessions per user: 5/week
- Average searches per session: 3
- AI analysis usage: 20% of users

**Revenue:**
- Ad revenue: $100+/month
- Premium subscribers: 10+
- Donation revenue: $20+/month

### 7.2 Growth Metrics (6개월)

**User Acquisition:**
- MAU: 5,000+
- DAU: 500+
- Retention Rate (D30): 20%+

**Engagement:**
- Average sessions per user: 10/week
- Average searches per session: 5
- AI analysis usage: 30% of users

**Revenue:**
- Ad revenue: $400+/month
- Premium subscribers: 50+
- Donation revenue: $50+/month
- **Total:** $500+/month

### 7.3 KPIs

**Product KPIs:**
- Search speed: < 5 seconds (YouTube API)
- AI analysis speed: < 10 seconds
- App crash rate: < 1%
- API success rate: > 95%

**Business KPIs:**
- Customer Acquisition Cost (CAC): $0 (organic)
- Lifetime Value (LTV): $10+ (ads + subs)
- Churn rate: < 10%/month
- Net Promoter Score (NPS): 40+

---

## 8. Risks & Mitigations

### 8.1 Technical Risks

**Risk 1: YouTube API Quota**
- **Probability:** Medium
- **Impact:** High (검색 불가)
- **Mitigation:**
  - Mock 모드 fallback
  - Daily quota monitoring
  - Cache YouTube results (24시간)

**Risk 2: POB 링크 변경**
- **Probability:** Low
- **Impact:** Medium (파싱 실패)
- **Mitigation:**
  - Regex 패턴 업데이트
  - 에러 로깅 및 알림

**Risk 3: AI API 비용**
- **Probability:** Low (사용자 API 키)
- **Impact:** Low
- **Mitigation:**
  - 사용자 책임 명시
  - 토큰 사용량 표시

### 8.2 Business Risks

**Risk 1: 낮은 사용자 전환율**
- **Probability:** Medium
- **Impact:** High (수익 감소)
- **Mitigation:**
  - 무료 기능 강화 (경쟁력)
  - 3일 무료 체험
  - 명확한 가치 제안

**Risk 2: 경쟁 제품 등장**
- **Probability:** Medium
- **Impact:** Medium
- **Mitigation:**
  - AI 분석 차별화
  - 빠른 feature 업데이트
  - 커뮤니티 피드백 반영

### 8.3 Legal Risks

**Risk 1: API 약관 위반**
- **Probability:** Low
- **Impact:** High (서비스 중단)
- **Mitigation:**
  - 사용자 API 키 모델 (재판매 ❌)
  - 약관 정기 검토

**Risk 2: 광고 정책 위반**
- **Probability:** Low
- **Impact:** Medium (광고 수익 중단)
- **Mitigation:**
  - AdSense 정책 준수
  - 정기 검토

---

## 9. Competitive Analysis

### 9.1 Competitors

#### poebuilds.cc
**Strengths:**
- 오래된 커뮤니티
- 다양한 빌드

**Weaknesses:**
- 느린 속도
- 오래된 UI
- 검색 기능 약함

**PathcraftAI 우위:**
- ⚡ 10배 빠른 검색 (YouTube API)
- 🤖 AI 분석
- 💰 실시간 가격 정보

#### POE Ninja
**Strengths:**
- 정확한 가격 정보
- 메타 통계

**Weaknesses:**
- 빌드 가이드 없음
- 초보자 진입 장벽

**PathcraftAI 우위:**
- 📺 YouTube 가이드 통합
- 🤖 AI 초보자 가이드
- 📚 북마크 기능

#### POE Overlay
**Strengths:**
- 인게임 오버레이
- 무료

**Weaknesses:**
- 빌드 검색 없음
- 가격 정보만

**PathcraftAI 우위:**
- 🔍 빌드 검색
- 🤖 AI 분석
- 📖 가이드 생성

### 9.2 Differentiation

**Unique Value Propositions:**

1. **AI-Powered Analysis**
   - 경쟁사 없음
   - GPT/Gemini/Claude 3종 지원
   - 한국어 분석

2. **Integrated Search**
   - YouTube + poe.ninja 통합
   - 영상 + 가격 + POB 한번에
   - 빠른 속도 (< 5초)

3. **User-Friendly**
   - 초보자 친화적
   - 북마크 관리
   - 다크/라이트 테마

---

## 10. Future Vision (1년 후)

### 10.1 Product Evolution

**Phase 5: Mobile App (Q2 2026)**
- Android/iOS 앱 개발
- 크로스 플랫폼 (Xamarin/MAUI)
- 모바일 광고 수익

**Phase 6: Web Version (Q3 2026)**
- Blazor WebAssembly
- 브라우저 확장 프로그램
- 더 넓은 사용자층

**Phase 7: Community Features (Q4 2026)**
- 사용자 빌드 공유
- 빌드 평가 (별점)
- 댓글 시스템

### 10.2 Revenue Projection

**Year 1 (2026):**
- MAU: 10,000+
- Revenue: $1,000+/month
- Premium subscribers: 100+

**Year 2 (2027):**
- MAU: 50,000+
- Revenue: $5,000+/month
- Premium subscribers: 500+

### 10.3 Exit Strategy (선택사항)

**Option 1: Acquisition**
- 타겟: GGG (POE 개발사) 또는 유사 회사
- 시점: 사용자 50,000+ 달성 시
- 예상 가치: $50,000-100,000

**Option 2: Sustainable Business**
- 독립 운영 지속
- 월 $5,000+ 수익 목표
- 개발자 풀타임 전환 가능

---

## Appendix

### A. API Cost Estimation

**OpenAI GPT-4o:**
- Input: $2.50 / 1M tokens
- Output: $10.00 / 1M tokens
- Average analysis: 450 input + 620 output = $0.0073

**Google Gemini 1.5 Pro:**
- Input: $1.25 / 1M tokens
- Output: $5.00 / 1M tokens
- Average analysis: 450 input + 620 output = $0.0037

**Anthropic Claude 3.5 Sonnet:**
- Input: $3.00 / 1M tokens
- Output: $15.00 / 1M tokens
- Average analysis: 450 input + 620 output = $0.0107

**사용자 비용 (월 100회 분석):**
- GPT: $0.73/month
- Gemini: $0.37/month
- Claude: $1.07/month

→ 사용자 부담 매우 낮음 (✅ 경쟁력)

### B. Technology Alternatives

**Frontend:**
- ✅ WPF (선택): Windows native, 빠름
- ❌ Electron: 느림, 메모리 많이 사용
- ❌ Web: 크로스 플랫폼이지만 복잡

**Backend:**
- ✅ Python (선택): AI 라이브러리 풍부
- ❌ C# 전체: POB 파싱 라이브러리 부족
- ❌ Node.js: Python보다 AI 지원 약함

### C. FAQ

**Q: 왜 사용자가 API 키를 직접 발급해야 하나요?**
A: OpenAI 등의 API를 재판매하려면 Business 계약이 필요합니다. 사용자가 직접 발급하면 법적으로 안전하고, 비용도 저렴합니다 (월 $1 미만).

**Q: 광고 없이는 운영이 안 되나요?**
A: 서버 비용이 없어서 광고 없이도 가능하지만, 개발 지속을 위해 최소한의 수익이 필요합니다. 프리미엄 구독으로 광고를 제거할 수 있습니다.

**Q: POB 파일 업로드는 언제 지원되나요?**
A: Phase 4 (9-12주차)에 추가될 예정입니다. 우선 YouTube 검색 기반 MVP를 완성합니다.

**Q: 한국어만 지원하나요?**
A: 초기에는 한국어 우선이지만, Phase 4에서 영어 지원을 추가할 계획입니다.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-15
**Next Review:** 2025-12-01
**Owner:** PathcraftAI Team
