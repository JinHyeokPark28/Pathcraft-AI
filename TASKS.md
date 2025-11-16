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

### Phase 2: AI 기능 & 프리미엄 (Week 5-6)

#### API 키 설정 (무료 기능)
- [ ] **설정 화면**
  - [ ] API 키 입력 UI (GPT/Gemini/Claude)
  - [ ] 키 검증 기능
  - [ ] 로컬 암호화 저장
  - [ ] "발급 방법" 가이드 링크

- [ ] **Gemini API 통합**
  - [ ] Google Gemini 클라이언트 구현
  - [ ] Python 코드 작성
  - [ ] C# 연동

#### AI 분석 화면 (무료 기능)
- [ ] **분석 결과 UI**
  - [ ] 빌드 개요 섹션
  - [ ] 장점/단점 리스트
  - [ ] 추천 대상 표시
  - [ ] 핵심 시너지 하이라이트

- [ ] **AI 모델 선택**
  - [ ] 드롭다운 (GPT/Gemini/Claude)
  - [ ] 각 모델별 설정
  - [ ] 토큰 사용량 표시

#### 프리미엄 기능
- [ ] **3일 무료 체험**
  - [ ] 체험 시작 UI
  - [ ] 체험 기간 추적 (로컬 저장)
  - [ ] 체험 종료 알림

- [ ] **광고 제거 로직**
  - [ ] 프리미엄 상태 확인
  - [ ] 광고 표시/숨김 토글

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

### Phase 5: 인게임 오버레이 (Week 13-16) - 선택사항

#### 기본 오버레이
- [ ] **게임 감지 및 오버레이**
  - [ ] POE 프로세스 감지 (PathOfExile_x64.exe)
  - [ ] 투명 윈도우 생성 (WPF Layered Window)
  - [ ] Always-on-top 설정
  - [ ] 단축키 토글 (F10)
  - [ ] Ctrl+C 클립보드 감지

#### 가격 체크 (POE Overlay 기능)
- [ ] **아이템 가격 표시**
  - [ ] 클립보드에서 아이템 데이터 파싱
  - [ ] poe.ninja API 호출
  - [ ] 가격 오버레이 표시
  - [ ] 커런시/유니크/레어 지원

#### AI 아이템 추천 (🔥 킬러 기능)
- [ ] **캐릭터 상태 분석**
  - [ ] POE API로 현재 캐릭터 정보 읽기
  - [ ] 레벨, 저항, 생명력, ES 추출
  - [ ] POB 빌드 연동 (목표 장비)
  - [ ] 소지 커런시 파싱

- [ ] **AI "지금 쓸까?" 분석**
  - [ ] 레벨 단계 확인
    - Level 28 → Tabula Rasa 추천
    - Level 70 → 엔드게임 장비 필요
  - [ ] 저항 부족 감지
    - Cold 30% 부족 → 반지/목걸이 추천
  - [ ] 예산 고려
    - 소지금 50c → 100c 아이템 대안 제시
  - [ ] DPS/생존력 개선도 예측
  - [ ] Python AI 분석 스크립트 (ai_item_advisor.py)

- [ ] **대안 추천**
  - [ ] 저렴한 대안 아이템
  - [ ] 비슷한 옵션 검색
  - [ ] 업그레이드 경로 제시

#### 빌드 가이드 오버레이
- [ ] **레벨링 체크리스트**
  - [ ] F10 토글 UI
  - [ ] 다음 스킬 변경 알림
  - [ ] 다음 업그레이드 아이템
  - [ ] 완료 항목 체크

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

### Sprint 3 (Week 5-6): AI Features & Premium
- [ ] API 키 설정 UI (무료 기능)
- [ ] AI 분석 화면 (무료 기능)
- [ ] 3개 AI 모델 통합 (무료 기능)
- [ ] 3일 무료 체험 시스템
- [ ] 광고 제거 로직

### Sprint 4 (Week 7-8): Monetization
- [ ] 광고 SDK
- [ ] 구독 시스템
- [ ] 후원 연동

### Sprint 5 (Week 9-12): Advanced Features
- [ ] 빌드 디버거
- [ ] 단계별 로드맵
- [ ] 메타 분석

### Sprint 6 (Week 13-16): 인게임 오버레이 (선택)
- [ ] 기본 오버레이 (게임 감지, 투명 윈도우)
- [ ] 가격 체크 (POE Overlay 기능)
- [ ] AI 아이템 추천 (차별화 🔥)
- [ ] 빌드 가이드 오버레이

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

### M3: AI Features & Premium (Target: 2026-01-01)
- 3 AI models integrated (무료 기능)
- API key management (무료 기능)
- 3일 무료 체험 시스템
- Premium features ready

### M4: Public Beta (Target: 2026-01-15)
- Ads integrated
- Subscription system
- Community feedback

### M5: v1.0 Release (Target: 2026-02-01)
- All features complete
- Build debugger working
- Documentation complete

### M6: Overlay Release (Target: 2026-03-01) - 선택사항
- In-game overlay working
- AI item recommendation (🔥 킬러 기능)
- Price check integration
- Leveling guide overlay
- POE Overlay 완전 대체 가능

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

## 🎉 OAuth Approval (2025-11-16)

### GGG Official Approval ✅
- [x] **OAuth 2.1 승인 완료**
  - [x] Client Type: Public Client (PKCE)
  - [x] Scopes: profile, characters, stashes, league_accounts
  - [x] Approval Date: June 7, 2025
  - [x] poe_oauth.py 구현 완료 (이미 완성)
  - [x] README.md OAuth 설정 가이드 추가
  - [x] .gitignore에 poe_token.json 추가
  - [x] PROGRESS.md OAuth 승인 마일스톤 기록

**비즈니스 임팩트:**
- ✅ Freemium 모델 합법적 운영
- ✅ 유료 Tier 판매 가능
- ✅ 광고 수익 가능
- ✅ 후원 받기 가능
- ✅ 캐릭터 빌드 분석 가능

---

## 📋 Phase 7: Fine-tuned LLM Integration (2025-11-16)

### Phase 7.1: Smart Fallback Logic ✅
- [x] **build_guide_generator.py Fallback 개선**
  - [x] Fine-tuned 실패 시 GPT-4 Fallback
  - [x] GPT-4 실패 시 Mock Fallback
  - [x] 기존 Mock/GPT-4/Claude 기능 100% 유지
  - [x] 테스트: Mock guide generation
  - [x] requirements.txt에 openai, anthropic 추가

### Phase 7.2: Fine-tuning 데이터 수집 (계획)
- [ ] Reddit r/pathofexile 10,000 Q&A 수집
- [ ] YouTube 자막 1,000개 빌드 가이드
- [ ] POE Wiki 크롤링
- [ ] poe.ninja 메타 데이터 통합
- [ ] 데이터 정제 및 포맷팅

### Phase 7.3: Fine-tuning 실행 (계획)
- [ ] OpenAI Fine-tuning API 호출
- [ ] 모델 학습 (비용: $129)
- [ ] 품질 검증
- [ ] 모델 ID 획득: ft:gpt-3.5-turbo:pathcraftai:poe-expert-v1

### Phase 7.2: Hybrid 3-Tier Model Implementation (완료 - 2025-11-16) ✅

**3-Tier System:**
- [x] Free tier: User API keys (Gemini/OpenAI/Claude)
- [x] Premium tier: 20 AI credits/month ($2/month)
- [x] Expert tier: Unlimited Fine-tuned AI ($5/month)

**Code Implementation:**
- [x] build_guide_generator.py tier parameter
- [x] Gemini support (call_gemini function)
- [x] Credit system (check/deduct functions)
- [x] argparse validation (tier + user_id)
- [x] requirements.txt (google-generativeai)

**Testing:**
- [x] Free tier + Mock (working)
- [x] Free tier + Gemini (validation working)
- [x] Free tier + OpenAI (validation working)
- [x] Free tier + Claude (validation working)
- [x] Premium tier validation (user_id required)
- [x] Expert tier validation (user_id required)

**Documentation:**
- [x] README.md (3-tier pricing table + examples)
- [x] PRD.md Section 3.2 (Core Features)
- [x] PRD.md Section 7 (Pricing & Monetization)
- [x] .env.example (comprehensive setup guide)
- [x] PROGRESS.md (Phase 7.2 documentation)
- [x] TASKS.md (this file)

**Business Impact:**
- [x] Revenue model: $512/month profit (MAU 1,000)
- [x] Scalability: $2,666/month (MAU 5,000, 6 months)
- [x] Conversion strategy: AI preview → Premium (7x ROI)

### Phase 7.3: Fine-tuning 데이터 수집 (다음 단계)
- [ ] Reddit r/pathofexile Q&A 수집 (10,000+ posts)
- [ ] YouTube 자막 추출 (1,000+ videos)
- [ ] POE Wiki 스크래핑
- [ ] poe.ninja 메타 데이터
- [ ] OpenAI Fine-tuning 포맷 변환

### Phase 7.4: Fine-tuning 실행 (계획)
- [ ] 학습 데이터 업로드
- [ ] Fine-tuning job 실행
- [ ] 품질 검증 (vs GPT-4)
- [ ] 모델 ID 획득: ft:gpt-3.5-turbo:pathcraftai:poe-expert-v1
- [ ] 비용: ~$129

### Phase 7.5: Expert Tier 베타 (계획)
- [ ] 베타 테스터 10명 모집
- [ ] 피드백 수집
- [ ] Fine-tuned vs GPT-4 품질 비교
- [ ] 프롬프트 최적화

---

## 📋 Phase 8: Auto Patch Monitoring System (v1.1) - 2025-11-16

### 살아있는 AI - "Living AI" Differentiation

**Monitoring Sources:**
- Twitter (@pathofexile)
- Reddit (r/pathofexile GGG posts)
- POE Official Homepage RSS
- YouTube (GGG Channel)

**3-Stage Video Content Extraction:**
1. YouTube Transcript API (99% success - GGG provides English subtitles)
2. Video description fallback
3. OpenAI Whisper fallback (최후의 수단)

**Cost:** ~$3/month (매우 저렴!)
**Update Speed:** 3-7 days faster than competitors
**Automation:** Cron job at GGG NZ time (9 AM NZ = 5 AM Korea)

### Priority 1: Core Implementation ⏳
- [x] **video_transcript.py** (완료 - 2025-11-16)
  - [x] extract_video_id() - YouTube URL 파싱
  - [x] get_transcript_stage1() - YouTube Transcript API
  - [x] get_description_stage2() - Video description fallback
  - [x] get_whisper_stage3() - Whisper fallback (stub)
  - [x] extract_video_content() - 3-stage orchestration
  - [x] 파일: `video_transcript.py` (262 lines)

- [x] **patch_monitor.py** (완료 - 2025-11-16)
  - [x] PatchMonitor 클래스
  - [x] monitor_youtube() - GGG channel monitoring
  - [x] monitor_twitter() - @pathofexile monitoring
  - [x] monitor_reddit() - r/pathofexile GGG posts
  - [x] monitor_rss() - POE homepage RSS
  - [x] analyze_patch() - GPT-4 patch analysis
  - [x] should_update_pathcraft() - Auto-update decision
  - [x] monitor_all_sources() - Unified monitoring
  - [x] 파일: `patch_monitor.py` (486 lines)

- [x] **requirements.txt** (완료 - 2025-11-16)
  - [x] youtube-transcript-api>=0.6.0
  - [x] tweepy>=4.14.0
  - [x] feedparser>=6.0.0
  - [x] psutil>=5.9.0

- [x] **.env.example** (완료 - 2025-11-16)
  - [x] TWITTER_BEARER_TOKEN
  - [x] REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET
  - [x] GGG_RSS_URL
  - [x] PATCH_MONITOR_CRON
  - [x] DISCORD_WEBHOOK_ERRORS / DISCORD_WEBHOOK_PATCHES

- [ ] **Cron Job Setup**
  - [ ] Cron schedule: 0 5 * * * (5 AM Korea = 9 AM NZ)
  - [ ] Shell script wrapper
  - [ ] Logging to file
  - [ ] Error notification (Discord webhook)

- [ ] **Testing**
  - [ ] Test video content extraction (GGG video)
  - [ ] Test Twitter API (recent @pathofexile tweets)
  - [ ] Test Reddit API (r/pathofexile GGG posts)
  - [ ] Test RSS feed parsing
  - [ ] Test GPT-4 patch analysis
  - [ ] End-to-end test (full monitoring cycle)

### Priority 2: Discord Notifications 📋
- [ ] **Discord Webhook Integration**
  - [ ] Send patch notification to Discord
  - [ ] Format as Discord Embed
  - [ ] Include severity (critical/major/minor/hotfix)
  - [ ] Include impact summary
  - [ ] Include auto-update status
  - [ ] Error notifications to #errors channel

- [ ] **Notification Templates**
  - [ ] Critical patch template
  - [ ] Major patch template
  - [ ] Hotfix template
  - [ ] Error notification template

### Priority 3: Auto-Update PathcraftAI 📋
- [ ] **Build Data Auto-Update**
  - [ ] Trigger data refresh on major patches
  - [ ] Update poe.ninja item prices
  - [ ] Refresh YouTube build searches
  - [ ] Update patch notes database

- [ ] **AI Model Update**
  - [ ] Regenerate AI prompts with new patch info
  - [ ] Update meta trends
  - [ ] Update skill/item recommendations

### Priority 4: Error Monitoring (선택 - Discord Integration)
- [ ] **Lightweight Error Logger (Python)**
  - [ ] Global exception handler
  - [ ] Performance monitoring (memory, CPU)
  - [ ] Batch error reporting
  - [ ] Critical error immediate notification

- [ ] **Error Logger (C# WPF)**
  - [ ] Global WPF exception handler
  - [ ] Async error reporting
  - [ ] User anonymization (MAC hash)

- [ ] **AWS Lambda Error Handler**
  - [ ] Error aggregation
  - [ ] Discord webhook sender
  - [ ] DynamoDB storage
  - [ ] SMS alert for critical errors (선택)

### Implementation Notes

**GGG Timezone:**
- New Zealand (NZDT): UTC+13
- Korea: UTC+9
- 9 AM NZ = 5 AM Korea = 4 PM UTC (previous day)

**Cron Expression:**
```bash
# Run daily at 5 AM Korea time (9 AM NZ time)
0 5 * * * /path/to/pathcraftai/patch_monitor.sh
```

**Cost Breakdown:**
- YouTube Transcript API: FREE
- Twitter API v2: FREE (500k tweets/month)
- Reddit API: FREE
- RSS: FREE
- GPT-4 analysis: ~$0.03/patch × 2 patches/week × 4 weeks = $0.24/month
- OpenAI Whisper: ~$0.12/video (rarely used)
- **Total:** ~$3/month

**Differentiation:**
- Competitors rely on manual updates (3-7 days lag)
- PathcraftAI auto-updates within hours
- "살아있는 AI" - Always current with meta

**Success Metrics:**
- Patch detection latency: < 1 hour
- False positive rate: < 5%
- Auto-update accuracy: > 95%
- Cost: < $5/month

---

**Next Action:** Phase 8 Priority 1 Cron Job Setup OR Phase 8 Priority 2 Discord Notifications
