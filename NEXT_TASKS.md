# PathcraftAI - 다음 작업 목록

## ✅ 완료된 작업 (2025-01-16)

### 1. OAuth 2.1 인증 시스템
- [x] PKCE 기반 OAuth 2.1 구현
- [x] POE 계정 연동 (account:profile, account:characters, account:stashes, account:leagues)
- [x] 토큰 저장 및 자동 갱신
- [x] UI 연동 ("Connect POE Account" 버튼)

### 2. 사용자 빌드 분석 엔진
- [x] 캐릭터 아이템 데이터 파싱
- [x] 유니크 아이템 추출 및 분석
- [x] 6링크 감지 및 메인 스킬 파악
- [x] 빌드 타입 자동 추론 (유니크 > 스킬 > 클래스)
- [x] POE.Ninja 기반 아이템 가치 계산
- [x] 빌드별 맞춤 업그레이드 제안

### 3. UI 통합
- [x] "Your Current Build" 섹션 추가
- [x] 빌드 정보 표시 (캐릭터, 빌드 타입, 스킬, 아이템 가치)
- [x] 업그레이드 제안 표시

---

## 🔥 우선순위 높음 - 베트남에서 할 작업

### 1. POE.Ninja 데이터 수집 자동화 ⭐⭐⭐
**현재 상태**: `poe_ninja_fetcher.py`는 있지만 데이터가 없음
**해야 할 일**:
```bash
cd src/PathcraftAI.Parser
.venv/Scripts/python.exe poe_ninja_fetcher.py --collect
```
- [ ] POE.Ninja에서 유니크 아이템 가격 수집 (unique_weapons.json, unique_armours.json, unique_accessories.json)
- [ ] 스킬 젬 가격 수집 (skill_gems.json)
- [ ] 매일 자동 갱신 스케줄러 추가 (Windows Task Scheduler 또는 cron)
- [ ] 데이터 저장 경로: `src/PathcraftAI.Parser/game_data/`

### 2. YouTube 빌드 데이터 수집 ⭐⭐⭐
**현재 상태**: `popular_build_collector.py` 코드는 완성
**해야 할 일**:
```bash
cd src/PathcraftAI.Parser
.venv/Scripts/python.exe popular_build_collector.py --league Keepers --version 3.27
```
- [ ] YouTube API 키 발급 (Google Cloud Console)
- [ ] 환경변수 설정 (`YOUTUBE_API_KEY`)
- [ ] POE.Ninja + YouTube 통합 빌드 데이터베이스 생성
- [ ] 데이터 저장: `src/PathcraftAI.Parser/build_data/popular_builds_Keepers.json`
- [ ] 리그 시작마다 수집 (3개월에 1번)

### 3. Privacy 설정 문제 해결 ⭐⭐
**현재 문제**:
- 사용자 캐릭터 아이템이 Privacy 설정으로 인해 0개 반환됨
- 빌드 분석이 작동하지 않음

**해결 방안**:
1. **UI에 안내 메시지 추가**:
   - "Your Current Build" 섹션에 Privacy 설정 가이드 표시
   - POE 설정 페이지 링크 제공
   - "Character items are hidden. Please enable 'Show characters' in your POE privacy settings."

2. **Privacy 설정 체크 자동화**:
   ```python
   # analyze_user_build.py에 추가
   if len(items) == 0:
       return {
           "error": "privacy_restricted",
           "message": "Character items are hidden. Please check your POE privacy settings.",
           "help_url": "https://www.pathofexile.com/my-account/privacy"
       }
   ```

3. **UI 업데이트**:
   - Privacy 에러 시 도움말 표시
   - 설정 변경 후 "Refresh" 버튼으로 재시도

### 4. 빌드 추천 로직 개선 ⭐⭐
**현재**: Mock 데이터 기반 추천
**목표**: 실제 POE.Ninja + YouTube 데이터 기반 추천

**해야 할 일**:
- [ ] `get_popular_builds()` 함수에서 실제 데이터 로드 확인
- [ ] 빌드 카테고리별 추천 로직:
  - "upgrades": 사용자 빌드 기반 업그레이드 (이미 완료)
  - "popular": POE.Ninja 인기 빌드 (상위 20개)
  - "streamer": YouTube 조회수 높은 빌드
  - "meta": 현재 메타 빌드 (클래스별)
- [ ] 리그 단계별 추천 (Early, Mid, Late)

### 5. 빌드 카드 UI 개선 ⭐
**현재**: 텍스트만 표시
**목표**: 이미지, 아이콘, 가격 정보 추가

**해야 할 일**:
- [ ] POE.Ninja 아이템 아이콘 URL 표시
- [ ] YouTube 썸네일 표시
- [ ] POB (Path of Building) 링크 버튼 추가
- [ ] 빌드 가격대 표시 (Budget, Mid-tier, High-end)
- [ ] 클릭 시 YouTube 영상 자동 재생

---

## 📋 중간 우선순위

### 6. POB (Path of Building) 파싱 연동
**목표**: YouTube 영상 설명에서 POB 링크 추출 및 파싱

**해야 할 일**:
- [ ] `pobapi` 라이브러리 활용
- [ ] POB 링크에서 빌드 데이터 추출:
  - 패시브 트리
  - 스킬 젬 링크
  - 아이템 설정
  - DPS, Life, ES 등 스탯
- [ ] UI에 POB 빌드 미리보기 표시

### 7. 스트리머 빌드 캐싱
**현재**: `get_streamer_builds_cached()` 함수 있지만 데이터 없음

**해야 할 일**:
- [ ] 주요 POE 스트리머 목록 작성:
  - Zizaran
  - Mathil
  - Alkaizerx
  - Quin69
  - RaizQT
- [ ] YouTube 채널 ID로 최신 빌드 영상 수집
- [ ] 캐시 저장: `build_data/streamer_builds/index_Keepers.json`
- [ ] 주간 자동 갱신

### 8. 리그 단계 자동 감지 개선
**현재**: `detect_league_phase()` 함수 있음
**개선점**:
- [ ] POE API에서 리그 시작/종료 날짜 자동 로드
- [ ] 단계별 추천 알고리즘 조정:
  - **Early** (1주 이내): Budget/League Starter 빌드
  - **Mid** (1-4주): Mid-tier 빌드
  - **Late** (1개월+): End-game 빌드

### 9. 에러 핸들링 개선
**해야 할 일**:
- [ ] POE API Rate Limit 대응 (429 에러)
- [ ] OAuth 토큰 만료 시 자동 갱신
- [ ] YouTube API 할당량 초과 대응
- [ ] 네트워크 실패 시 재시도 로직

---

## 🔮 낮은 우선순위 (나중에)

### 10. 고급 기능
- [ ] 빌드 비교 기능 (현재 빌드 vs 추천 빌드)
- [ ] 업그레이드 경로 시각화 (단계별 아이템 순서)
- [ ] 예산별 필터링 (10c, 50c, 1 divine, 10 divine+)
- [ ] 클래스별 필터
- [ ] 스킬 타입별 필터 (공격, 마법, 소환수)

### 11. 소셜 기능
- [ ] 빌드 저장 및 공유
- [ ] 커뮤니티 빌드 투표/평가
- [ ] Discord 연동

### 12. 프리미엄 기능
- [ ] 광고 제거 ($2.50/month)
- [ ] 고급 빌드 분석
- [ ] 실시간 시장 가격 알림
- [ ] POB 자동 업데이트

---

## 🛠️ 기술 부채

### 코드 정리
- [ ] `ladder_cache_builder.py` 제거 (더 이상 사용 안 함)
- [ ] Mock 데이터 제거
- [ ] 에러 로깅 추가 (Python logging 모듈)
- [ ] 단위 테스트 작성

### 성능 최적화
- [ ] POE.Ninja 데이터 캐싱 (메모리)
- [ ] 빌드 데이터 압축 저장
- [ ] UI 로딩 속도 개선 (비동기 로딩)

---

## 📝 베트남에서 작업 시작하는 법

### 1. 환경 설정
```bash
cd C:\Users\vnddn\OneDrive\Desktop\프로그래밍자료\Unity\PathcraftAI
git pull
```

### 2. POE.Ninja 데이터 수집 (최우선!)
```bash
cd src/PathcraftAI.Parser
.venv/Scripts/python.exe poe_ninja_fetcher.py --collect
```

확인:
```bash
dir game_data
# unique_weapons.json, unique_armours.json, unique_accessories.json, skill_gems.json 있어야 함
```

### 3. YouTube 빌드 데이터 수집
```bash
# YouTube API 키 설정 (.env 파일)
echo YOUTUBE_API_KEY=your_api_key_here > .env

# 빌드 데이터 수집
.venv/Scripts/python.exe popular_build_collector.py --league Keepers --version 3.27
```

확인:
```bash
dir build_data
# popular_builds_Keepers.json 있어야 함
```

### 4. 앱 실행 및 테스트
```bash
cd ../..
dotnet run --project src/PathcraftAI.UI
```

테스트 시나리오:
1. "Connect POE Account" 클릭 → OAuth 인증
2. "Refresh Recommendations" 클릭
3. "Your Current Build" 섹션에 빌드 정보 표시 확인
4. 추천 빌드 목록 확인 (실제 YouTube 데이터)

---

## 🐛 알려진 버그

1. **Privacy 설정 문제** ⭐⭐⭐
   - 증상: 아이템 0개 반환
   - 해결: UI에 안내 메시지 추가 필요

2. **Mock 데이터 사용**
   - 증상: "Death's Oath Occultist" 등 가짜 빌드만 표시
   - 해결: POE.Ninja + YouTube 데이터 수집 필요

3. **YouTube API 미설정**
   - 증상: `popular_build_collector.py` 실행 실패
   - 해결: YouTube API 키 발급 및 설정

---

## 📚 참고 문서

- [OAUTH_SETUP.md](Docs/OAUTH_SETUP.md) - OAuth 인증 가이드
- [POE OAuth Docs](https://www.pathofexile.com/developer/docs/authorization)
- [POE.Ninja API](https://poe.ninja/api)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [pobapi Documentation](https://github.com/ppoelzl/PathOfBuildingAPI)

---

## 💡 다음 마일스톤

### Milestone 1: 실제 데이터 기반 추천 (1-2일)
- [x] OAuth 인증
- [x] 사용자 빌드 분석 엔진
- [ ] POE.Ninja 데이터 수집
- [ ] YouTube 빌드 데이터 수집
- [ ] 실제 데이터 기반 추천 표시

### Milestone 2: UX 개선 (3-5일)
- [ ] Privacy 안내 메시지
- [ ] 빌드 카드 UI 개선
- [ ] POB 링크 연동
- [ ] 이미지/아이콘 표시

### Milestone 3: 자동화 및 최적화 (1주)
- [ ] 데이터 수집 자동화
- [ ] 에러 핸들링 개선
- [ ] 캐싱 및 성능 최적화

---

**다음에 시작할 때**: 위의 "베트남에서 작업 시작하는 법" 섹션부터 시작하세요!
