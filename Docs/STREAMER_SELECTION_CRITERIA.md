# Streamer/YouTuber 선정 기준

> PathcraftAI에서 지원하는 스트리머/유튜버 선정 기준 문서

**마지막 업데이트:** 2025-11-21 (데이터 수집 기반)
**다음 리뷰:** 2026-02 (분기별)

---

## 개요

PathcraftAI는 POE 커뮤니티의 유명 스트리머와 유튜버의 빌드를 검색할 수 있습니다.
이 문서는 지원 스트리머 선정 기준과 관리 프로세스를 정의합니다.

---

## 기본 요구사항

모든 스트리머는 다음 조건을 충족해야 합니다:

1. **언어**: 영어 또는 한국어로 콘텐츠 제작
2. **콘텐츠 비중**: POE 관련 영상이 채널의 주요 콘텐츠 (10% 이상)
3. **활동 상태**: 최근 6개월 내 POE 영상 업로드 이력

---

## Tier 분류 기준

### Tier 1: 핵심 스트리머

**기준:**
- 구독자: 50,000+
- 최근 3개월 내 POE 영상: **30개+**
- 평균 조회수: **5,000+**

**특징:**
- 리그 시작 시 일 3-5개 업로드
- 평상시 주 5-10개 업로드
- 커뮤니티 인지도 최상위

**예시:**
| 스트리머 | 구독자 | 특징 |
|---------|--------|------|
| Zizaran | 400K+ | 리그당 100+ 영상 |
| Mathil | 200K+ | 리그당 50+ 영상 |
| Pohx | 100K+ | RF 전문 |
| GhazzyTV | 100K+ | 미니언 전문 |
| 게이머 비누 | 65K | 한국 1위 |
| POEASY | 62K | 한국 2위 |
| 엠피스 | 60K | 한국 3위 |

---

### Tier 2: 활성 스트리머

**기준:**
- 구독자: 10,000+
- 최근 2개월 내 POE 영상: **15개+**
- 평균 조회수: **2,000+**

**특징:**
- 리그 기간 주 5-7개 업로드
- 특정 분야 전문성

**예시:**
| 스트리머 | 구독자 | 특징 |
|---------|--------|------|
| Steelmage | 50K+ | 레이스 전문 |
| jungroan | 50K+ | |
| Empyrean | 50K+ | 그룹 파밍 |
| 추봉이 | 31K | 한국 |
| 뀨튜브 | 31K | 한국 |

---

### Tier 3: 커뮤니티 스트리머

**기준:**
- 구독자: 1,000+
- 최근 1개월 내 POE 영상: **5개+**
- 평균 조회수: **500+**

**특징:**
- 꾸준한 업로드
- 커뮤니티 추천

**예시:**
| 스트리머 | 구독자 | 특징 |
|---------|--------|------|
| tytykiller | - | 레이스 전문 |
| Ben | - | 레이스 전문 |
| 개굴덱 | - | 한국 |
| 산들바람 | - | 한국 |

---

## 자동 제외 기준

다음 조건에 해당하면 리스트에서 제외:

1. **90일 이상 POE 영상 업로드 없음**
2. **구독자 1,000 미만**
3. **POE 콘텐츠 비중 10% 미만**
4. **리그 시작 후 2주 내 영상 0개** (시즌 비활성)

---

## 업로드 패턴 참고

활발한 스트리머들의 일반적인 업로드 패턴:

| 스트리머 | 리그 시작 | 평상시 | 비고 |
|---------|----------|--------|------|
| Zizaran | 일 3-5개 | 주 5-10개 | 빌드 가이드 + 리뷰 |
| Mathil | 일 2-3개 | 주 10-15개 | 다양한 빌드 |
| GhazzyTV | 일 1-2개 | 주 5-7개 | 가이드 위주 |
| 한국 유튜버 | 일 1개 | 주 2-5개 | 상대적으로 적음 |

---

## 관리 프로세스

### 분기별 리뷰 (1월, 4월, 7월, 10월)

1. **데이터 수집**
   - YouTube API로 구독자 수 확인
   - 최근 90일 영상 개수 확인
   - 평균 조회수 계산

2. **평가**
   - Tier 기준에 맞는지 확인
   - 자동 제외 기준 해당 여부 확인

3. **업데이트**
   - 기준 미달 스트리머 제거
   - 신규 스트리머 추가
   - Tier 변경 반영

4. **문서 업데이트**
   - `auto_recommendation_engine.py` 매핑 수정
   - 이 문서의 "마지막 업데이트" 날짜 수정

### 신규 스트리머 추가 절차

1. GitHub Issue 또는 Discord에서 추천 접수
2. 기준 충족 여부 확인
3. 적절한 Tier 분류
4. 코드 및 문서 업데이트

### 스트리머 제거 절차

1. 자동 제외 기준 해당 시 자동 제거
2. 커뮤니티 피드백 반영 (부정확한 정보 등)
3. 코드 및 문서 업데이트

---

## YouTube API 고려사항

### 할당량

- 일일 한도: 10,000 units
- 검색당 비용: ~110 units
- 현재 사용량: ~4,000 units/day (40%)

### 지원 가능 스트리머 수

- 현재: 37명
- 최대 권장: 60-80명
- 초과 시 캐시 TTL 조정 필요

### 캐시 전략

- 기본 TTL: 24시간
- Tier 3는 48시간으로 연장 가능

---

## 현재 지원 스트리머

### 영어 (40명)

**Tier 1 (12명):** Zizaran, Pohx, GhazzyTV, Palsteron, jungroan, Empyrean, FastAF, Lolcohol, Fubgun, sirgog, ds_lily

**Tier 2 (11명):** Mathil, Crouching_Tuna, Ruetoo, Steelmage, spicysushi, Havoc616, Alkaizer, Waggle, BalorMage, DonTheCrown

**Tier 3 (9명):** Goratha, Imexile, CuteDog, RaizQT, nugiyen, tytykiller, Quin69, Kay Gaming

**비활성 (Twitch 전용):** Darkee, Lightee, Octavian0, Ben, Subtractem, GrimroTV, Path of Matth, Tarke Cat, Tripolar Bear, Fyregrass

### 한국어 (11명)

**Tier 1 (2명):** 게이머 비누, POEASY

**Tier 2 (6명):** 추봉이, 뀨튜브, 로나의 게임채널, 스테TV, 까까모리, 개굴덱

**Tier 3 (3명):** 엠피스, 혜미 Ham, 스탠다드QK

**비활성:** 산들바람, 닛쿄, 새봄추, 풍월량, 녹두로, 옥냥이

---

## 관련 파일

- 코드: `src/PathcraftAI.Parser/auto_recommendation_engine.py`
  - `STREAMER_CRITERIA` 딕셔너리
  - `STREAMER_YOUTUBE_CHANNELS` 딕셔너리
- 캐시: `src/PathcraftAI.Parser/build_data/youtube_cache/`

---

## 문의

- GitHub Issues: https://github.com/your-repo/PathcraftAI/issues
- 스트리머 추천도 Issue로 접수해주세요

---

**작성자:** PathcraftAI Team
**버전:** 1.0
