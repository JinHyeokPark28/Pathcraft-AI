# Path of Exile AI 빌드 최적화 연구 자료

> 작성일: 2025년 11월 23일  
> 목적: PathcraftAI 개발 참고 자료  
> 분류: 학술 논문, 기술 프로젝트, 오픈소스 도구

---

## 📋 목차

1. [개요](#1-개요)
2. [학술 논문 및 연구](#2-학술-논문-및-연구)
3. [기술 프로젝트 (오픈소스)](#3-기술-프로젝트-오픈소스)
4. [AI 빌드 도구 및 서비스](#4-ai-빌드-도구-및-서비스)
5. [관련 게임 AI 연구](#5-관련-게임-ai-연구)
6. [데이터셋 및 API](#6-데이터셋-및-api)
7. [핵심 기술 및 알고리즘](#7-핵심-기술-및-알고리즘)
8. [미개척 연구 영역](#8-미개척-연구-영역)
9. [참고 링크](#9-참고-링크)

---

## 1. 개요

### 1.1 연구 분야 분류

Path of Exile의 AI 관련 연구는 크게 3가지 방향으로 구분됩니다:

| 분야 | 설명 | 기술 스택 | 연구 현황 |
|------|------|-----------|-----------|
| **게임플레이 AI** | 화면 인식 기반 자동 플레이 | CNN, 강화학습 | 개인 프로젝트 수준 |
| **빌드 추천 AI** | 플레이어 맞춤 빌드 제안 | 추천 시스템, LLM | 상용 서비스 존재 |
| **패시브 트리 최적화** | 조건 기반 최적 노드 선택 | 유전 알고리즘, 최적화 | 오픈소스 진행 중 |

### 1.2 PoE 빌드 최적화의 복잡성

- **패시브 트리**: 1,300+ 노드, 시작점 7개
- **스킬 젬**: 200+ 액티브, 150+ 서포트 젬
- **아이템**: 1,000+ 유니크 아이템
- **어센던시**: 19개 클래스 (PoE1 기준)
- **검색 공간**: 사실상 무한대 (조합론적 폭발)

### 1.3 학술 연구 현황

⚠️ **중요**: Path of Exile을 직접 다룬 peer-reviewed 학술 논문은 **극히 드묾**
- 정식 논문: 2편 확인 (2018, 2022)
- 학위 논문: 2-3편 (PoE를 사례로 언급)
- GDC 발표: 2편 (GGG 공식)

---

## 2. 학술 논문 및 연구

### 2.1 정식 학술 논문 (Peer-Reviewed)

#### 📄 "Tedious by Design: Institutionalized Labor of Content Creators in the GaaS Model"

| 항목 | 내용 |
|------|------|
| **저널** | Przegląd Kulturoznawczy (Arts & Cultural Studies Review) |
| **연도** | 2022, Issue 4 (54), pp. 527-547 |
| **DOI** | https://doi.org/10.4467/20843860PK.22.036.17090 |
| **저자** | University of Social Sciences and Humanities (Warsaw, Poland) |
| **주제** | GaaS 모델에서 콘텐츠 크리에이터 노동 분석 |

**핵심 개념**:
- **Transactional Play**: 플레이 시간의 상품화
- **Aspirational Boredom**: 실제 플레이를 방송 영상으로 대체
- **Gaming the Markets**: 게임 내 경제에 적극적 영향

**연구 방법**:
- PoE 콘텐츠 크리에이터와의 심층 반구조화 인터뷰
- Twitch, YouTube 등 플랫폼 데이터 분석

**링크**:
- [ResearchGate](https://www.researchgate.net/publication/369437594)
- [ejournals.eu](https://ejournals.eu/en/journal/przeglad-kulturoznawczy/article/tedious-by-design)

---

#### 📄 "Aesthetics and Cosmetic Microtransactions in Path of Exile"

| 항목 | 내용 |
|------|------|
| **학회** | DiGRA 2018 |
| **저자** | Felczak M. |
| **주제** | 코스메틱 마이크로트랜잭션의 미학적 역할 분석 |

**이론적 프레임워크**:
- Jacques Rancière의 예술의 미학적 체제
- Nicholas Bourriaud의 관계 미학

**마이크로트랜잭션의 3가지 역할**:
1. 플레이어 간 사회적 상호작용의 기호 (Signifiers)
2. 특정 플레이 방식을 동기 부여하는 보상 (Awards)
3. 전통적 플레이 프레임 외부에서의 에이전시 도구 (Tools of Agency)

**링크**: [DiGRA Digital Library](http://www.digra.org/digital-library/keywords/path-of-exile/)

---

### 2.2 학위 논문 (Thesis)

#### 📄 "A Guide to Designing Skill Trees"

| 항목 | 내용 |
|------|------|
| **유형** | Bachelor's Thesis |
| **저자** | Santeri Orava |
| **기관** | Theseus (핀란드) |
| **연도** | 2019년 8월 |

**PoE 관련 내용**:
- PoE의 방대한 스킬 트리를 복잡성 vs 사용성 사례로 분석
- "게임의 스킬 트리가 수많은 플레이어를 포기하게 만들면서도 최고의 기능으로 평가받는 역설"

**링크**: [Theseus Repository](https://www.theseus.fi/bitstream/handle/10024/192256/Orava_Santeri.pdf)

---

#### 📄 "Interactions Between Game Design and Procedural Level Generation"

| 항목 | 내용 |
|------|------|
| **유형** | Master's Thesis |
| **저자** | Yuheng Cai |
| **기관** | Northeastern University |

**PoE 관련 내용**:
- BSP(Binary Space Partitioning) 변형 사용
- Weighted room selection으로 의미 있는 경로 생성
- 던전 생성 알고리즘 분석에서 PoE를 사례로 언급

**링크**: [Northeastern Repository](https://repository.library.northeastern.edu/files/neu:m0455c71t/fulltext.pdf)

---

### 2.3 산업 컨퍼런스 발표 (GDC)

#### 🎤 "Designing Path of Exile to Be Played Forever" (GDC 2019)

| 항목 | 내용 |
|------|------|
| **발표자** | Chris Wilson (GGG 공동창립자) |
| **컨퍼런스** | GDC 2019, San Francisco |

**주요 내용**:
- 시즌 구조화 및 예측 가능한 릴리즈
- 콘텐츠 재사용을 통한 빠른 개발
- 절차적 생성으로 신선함 유지
- 다중 무작위성 축을 활용한 재플레이성
- 깊은 게임플레이 시스템 설계
- 장기적 커뮤니티 성장 전략

**링크**: [GDC Vault](https://gdcvault.com/play/1026459/Designing-Path-of-Exile-to)

---

#### 🎤 "Procedural World Generation in Path of Exile" (ExileCon)

| 항목 | 내용 |
|------|------|
| **발표자** | Rhys Abraham (GGG 시니어 프로그래머) |
| **컨퍼런스** | ExileCon 2019 |

**주요 내용**:
- Room 기반 레벨 생성
- Tile key 시스템
- Room overlapping으로 유기적 레이아웃 생성
- PoE2 지역 개선 사항 소개

**링크**: [YouTube - GGG Official](https://www.youtube.com/watch?v=2vl37WQMIWM)

---

## 3. 기술 프로젝트 (오픈소스)

### 3.1 게임플레이 AI

#### 🤖 PoE AI - Deep Learning Bot

| 항목 | 내용 |
|------|------|
| **저자** | Nicholas T. Smith |
| **연도** | 2017-2018 |
| **언어** | Python, TensorFlow |
| **상태** | Proof-of-concept |

**아키텍처**:
```
[게임 화면] → [CNN 분류기] → [내부 세계 표현] → [행동 결정]
```

**CNN 구성**:
1. **장애물 분류 CNN**: 셀에 장애물 있는지 판단
2. **객체 분류 CNN**: 적/아이템/빈공간 분류
3. **움직임 감지 CNN**: 살아있는 적 타겟팅용

**핵심 컴포넌트**:
- `ProjectionMap`: 3D↔2D 좌표 변환 (PoE용 보정 행렬)
- `ScreenViewer`: Windows API 기반 화면 캡처
- `TargetingSystem`: CNN 기반 이미지 분류

**링크**:
- [GitHub Repository](https://github.com/nogilnick/poeai)
- [Blog Series](https://nicholastsmith.wordpress.com/2017/07/08/a-deep-learning-based-ai-for-path-of-exile-a-series/)
- [YouTube Demo](https://www.youtube.com/channel/UCQKlX3Mm7Z3e3p9zZ0YzXYg)

**주의**: ToS 위반 가능성 있음, 연구 목적으로만 사용

---

#### 🧭 PoE Learning Layouts - Vision Transformer

| 항목 | 내용 |
|------|------|
| **저자** | kweimann |
| **연도** | 2023-2024 (추정) |
| **기술** | Vision Transformer (ViT) |
| **정확도** | 94.25% (α=45° 기준) |

**개요**:
- 미니맵 영상만으로 출구 방향 예측
- 수동 라벨링 없이 자동 데이터셋 생성

**작동 방식**:
1. 미니맵 영상 녹화 (존 진입 → 출구 도달)
2. 프레임 스티칭으로 전체 맵 재구성
3. 각 프레임에서 출구 방향 자동 계산
4. ViT 학습

**한계**:
- 미로 같은 복잡한 레이아웃에서 성능 저하
- 벽/장애물 개념 없음
- 다중 목표(퀘스트 아이템 → 출구) 미지원

**링크**:
- [GitHub](https://github.com/kweimann/poe-learning-layouts)
- [HuggingFace Model](https://huggingface.co/kweimann/poe-learning-layouts)
- [HuggingFace Dataset](https://huggingface.co/datasets/kweimann/poe-learning-layouts)

---

### 3.2 패시브 트리 최적화

#### 🌳 PoESkillTree - Full Tree Optimizer

| 항목 | 내용 |
|------|------|
| **프로젝트** | PoESkillTree |
| **기능** | 패시브 트리 플래너 + 최적화 |
| **알고리즘** | 유전 알고리즘 (Genetic Algorithm) |
| **상태** | 진행 중 (Issue #106) |

**목표**:
- 사용자가 지정한 기준에 따라 전체 트리 자동 생성
- life, mana, damage, cast speed 등 다중 목표 최적화

**기술적 접근**:
```
[사용자 기준] → [Fitness Function] → [유전 알고리즘] → [최적 트리]
```

**핵심 문제**:
1. **Fitness Function 설계**: life와 dps 점수를 어떻게 결합?
2. **UI/UX**: 수학 모르는 사용자도 쓸 수 있게
3. **성능**: Compute.cs의 계산 속도

**아이디어**:
- 노드 속성별 가치 지정 (Ctrl+클릭)
- 목표값 + 우선순위 설정
- Steiner points 검색 알고리즘 기반

**링크**:
- [GitHub Repository](https://github.com/PoESkillTree/PoESkillTree)
- [Issue #106 - Full Tree Optimizer](https://github.com/PoESkillTree/PoESkillTree/issues/106)

---

## 4. AI 빌드 도구 및 서비스

### 4.1 PoE2 Build Optimizer MCP (2025)

| 항목 | 내용 |
|------|------|
| **유형** | MCP Server + Web App |
| **AI 백엔드** | Anthropic Claude / OpenAI |
| **대상** | Path of Exile 2 |

**기능**:
- 자연어 쿼리로 빌드 추천
- 공식 PoE API 연동
- 장비/패시브/스킬 AI 추천
- PoB(Path of Building) 내보내기

**아키텍처**:
```
src/
├── mcp_server.py          # MCP 서버
├── api/
│   ├── poe_api.py         # 공식 API 클라이언트
│   ├── poe2db_scraper.py  # poe2db.tw 스크래퍼
│   └── rate_limiter.py    # API 레이트 리밋
├── calculator/
│   ├── damage_calc.py     # DPS 계산
│   ├── defense_calc.py    # 방어 계산
│   └── build_scorer.py    # 빌드 점수
├── optimizer/
│   ├── gear_optimizer.py  # 장비 최적화
│   ├── passive_optimizer.py # 패시브 최적화
│   └── trade_advisor.py   # 트레이드 추천
└── ai/
    ├── query_handler.py   # NLP 처리
    └── recommendation_engine.py # AI 추천
```

**링크**: [Glama MCP](https://glama.ai/mcp/servers/@HivemindOverlord/poe2-mcp)

---

### 4.2 GPT 기반 어시스턴트

| 도구 | 설명 | 링크 |
|------|------|------|
| **POE Builder** | AI 빌드 제작/최적화, 메타 분석 | [yeschat.ai](https://www.yeschat.ai/gpts-9t557I6IbWD-POE-Builder) |
| **Path of GPT** | PoE 전문 GPT, 용어/메카닉 설명 | [yeschat.ai](https://www.yeschat.ai/gpts-2OTocBS6jY-Path-of-GPT) |
| **POE2 Skills AI** | PoE2 전용 빌드 어시스턴트 | [poe2skills-ai.com](https://poe2skills-ai.com/) |

---

## 5. 관련 게임 AI 연구

PoE를 직접 다룬 학술 논문은 적지만, 유사한 문제를 다룬 연구들이 있습니다.

### 5.1 Hearthstone AI 최적화

#### 📄 "Optimizing Hearthstone Agents using an Evolutionary Algorithm"

| 항목 | 내용 |
|------|------|
| **저널** | Knowledge-Based Systems (2019) |
| **DOI** | 10.1016/j.knosys.2019.105032 |
| **성과** | CIG 2018 Hearthstone AI 대회 2위 (33명 중) |

**접근법**:
- 진화 알고리즘(EA)으로 에이전트 최적화
- 공진화적 자가 학습 (외부 스파링 파트너 불필요)
- 게임 내 모든 요소를 고려한 데이터 기반 의사결정

**시사점**:
- CCG에서 EA가 MCTS보다 우수한 성능 가능
- 다양한 덱 아키타입(Aggro, Combo, Control) 처리

**링크**: [ACM DL](https://dl.acm.org/doi/10.1016/j.knosys.2019.105032)

---

### 5.2 StarCraft Build Order 최적화

| 논문 | 학회/저널 | 연도 |
|------|-----------|------|
| Multi-objective GA for Build Order | KI-Künstliche Intelligenz | 2013 |
| Continual Online Evolutionary Planning | GECCO | 2017 |
| GP for Automatic Strategy Generation | CIG | 2015 |

**공통 접근법**:
- 유전 알고리즘 / 진화 전략
- 다목적 최적화 (자원, 시간, 유닛 균형)
- 온라인 학습 (게임 중 적응)

---

### 5.3 Action-RPG AI 최적화

#### 📄 "Optimization of AI Tactic in Action-RPG Game"

| 항목 | 내용 |
|------|------|
| **출판** | Springer, 2016 |
| **주제** | ARPG에서 스마트 AI로 게임 도전 증가 |

**기술**:
- Fuzzy Logic
- Monte Carlo Tree Search
- Utility Curves

**링크**: [Springer](https://link.springer.com/chapter/10.1007/978-981-287-988-2_14)

---

### 5.4 진화 알고리즘 기반 게임 디자인

#### 📄 "Supporting Game Design with Evolutionary Algorithms"

| 항목 | 내용 |
|------|------|
| **출처** | Game Developer (2024) |
| **주제** | EA로 게임 파라미터 최적화 및 밸런싱 |

**핵심 개념**:
- **Fitness Evaluation**: 게임 디자인 요구사항 반영
- **병렬화**: EA의 개체 평가 병렬 처리
- **시뮬레이션 규모**: EA는 수많은 시뮬레이션 필요

**링크**: [Game Developer](https://www.gamedeveloper.com/design/supporting-game-design-with-evolutionary-algorithms)

---

## 6. 데이터셋 및 API

### 6.1 공개 데이터셋

#### Kaggle: Path of Exile Game Statistic

| 항목 | 내용 |
|------|------|
| **업로더** | gagazet |
| **연도** | 2017년 10월 |
| **규모** | 59,000 플레이어 |
| **리그** | Harbinger League |

**컬럼 (추정)**:
- 캐릭터 클래스
- 레벨
- 리그 유형 (SC/HC)
- 어센던시

**⚠️ 주의**: 2017년 데이터로 현재 메타와 상이

**관련 노트북**:
- [Path of Exile players data exploration](https://www.kaggle.com/code/jonathanbouchet/path-of-exile-players-data-exploration) - Jonathan Bouchet
- [POE Statistics: An Exploration](https://www.kaggle.com/code/microtang/poe-path-of-exile-statistics-an-exploration) - microtang
- [POE Harbinger League vs Classes](https://www.kaggle.com/code/atfisnotatf/poe-harbinger-league-vs-classes)

**링크**: [Kaggle Dataset](https://www.kaggle.com/datasets/gagazet/path-of-exile-league-statistic)

---

### 6.2 실시간 데이터 소스

| 소스 | 유형 | 용도 | 링크 |
|------|------|------|------|
| **poe.ninja** | 경제/빌드 | 아이템 가격, 인기 빌드 | https://poe.ninja |
| **PoE Trade API** | 공식 API | 아이템 거래 검색 | https://www.pathofexile.com/developer/docs/api-resources |
| **poe2db.tw** | 데이터베이스 | 게임 데이터 마이닝 | https://poe2db.tw |
| **RePoE** | GitHub | 정적 게임 데이터 JSON | https://github.com/brather1ng/RePoE |

---

### 6.3 공식 API

**Path of Exile Developer API**:
- 계정/캐릭터 정보
- 스태시 탭
- 리그 래더
- 트레이드 검색

**제한사항**:
- Rate limiting 엄격
- OAuth 인증 필요
- 일부 데이터 비공개

**문서**: [PoE Developer Docs](https://www.pathofexile.com/developer/docs)

---

## 7. 핵심 기술 및 알고리즘

### 7.1 패시브 트리 최적화

#### 문제 정의

```
입력:
- 시작 클래스 (7개 중 택1)
- 사용 가능 포인트 (최대 ~123)
- 목표 스탯 (life%, dps, resistance 등)
- 가중치/우선순위

출력:
- 최적 노드 집합
- 연결된 트리 형태 유지
```

#### 알고리즘 옵션

| 알고리즘 | 장점 | 단점 |
|----------|------|------|
| **유전 알고리즘 (GA)** | 대규모 검색 공간 처리 | Fitness 설계 어려움 |
| **MCTS** | 순차적 의사결정에 강함 | 계산 비용 높음 |
| **강화학습** | 최적 정책 학습 | 학습 시간 긺 |
| **정수 계획법 (ILP)** | 최적해 보장 | NP-hard, 규모 제한 |
| **Greedy + Local Search** | 빠름, 구현 쉬움 | 지역 최적해 |

#### Fitness Function 설계 예시

```python
def fitness(tree, weights):
    stats = calculate_stats(tree)
    
    score = 0
    score += weights['life'] * stats['increased_life']
    score += weights['dps'] * stats['dps_multiplier']
    score += weights['resist'] * min(stats['res_fire'], stats['res_cold'], stats['res_light'])
    
    # 페널티: 필수 조건 미충족
    if stats['strength'] < required_str:
        score -= 1000
    
    return score
```

---

### 7.2 빌드 추천 시스템

#### 접근법

| 방법 | 설명 | 데이터 요구 |
|------|------|-------------|
| **협업 필터링** | 유사 플레이어 빌드 추천 | 플레이어-빌드 행렬 |
| **콘텐츠 기반** | 빌드 특성 매칭 | 빌드 메타데이터 |
| **하이브리드** | 위 두 방법 결합 | 둘 다 |
| **LLM 기반** | 자연어로 빌드 설명/추천 | 빌드 가이드 텍스트 |

#### poe.ninja 데이터 활용

```python
# 인기 빌드 분석
builds = fetch_poe_ninja_builds(league='current')

# 클러스터링으로 아키타입 분류
from sklearn.cluster import KMeans
archetypes = KMeans(n_clusters=10).fit(build_features)

# 유사 빌드 추천
from sklearn.neighbors import NearestNeighbors
nn = NearestNeighbors(n_neighbors=5).fit(build_features)
similar = nn.kneighbors(user_build)
```

---

### 7.3 아이템 가치 평가

#### 특성 엔지니어링

```python
item_features = {
    # 기본 스탯
    'total_life': flat_life + (str // 5),
    'total_resist': fire + cold + light,
    'dps_stats': phys_dmg + ele_dmg + attack_speed,
    
    # 희귀도
    'mod_tier_avg': sum(mod_tiers) / len(mods),
    'open_prefix': max_prefix - current_prefix,
    'open_suffix': max_suffix - current_suffix,
    
    # 메타 가치
    'meta_skill_synergy': check_meta_skills(mods),
    'unique_mod': has_unique_mod(mods)
}
```

#### 가격 예측 모델

```python
from sklearn.ensemble import GradientBoostingRegressor

model = GradientBoostingRegressor()
model.fit(item_features, item_prices)

predicted_price = model.predict(new_item_features)
```

---

## 8. 미개척 연구 영역

PoE AI 연구는 학술적으로 거의 다뤄지지 않아 **논문 주제로 적합**합니다.

### 8.1 연구 아이디어

| 주제 | 접근법 | 데이터 소스 | 난이도 |
|------|--------|-------------|--------|
| **패시브 트리 최적화** | 다목적 GA + Pareto front | PoB 데이터 | ⭐⭐⭐ |
| **빌드 추천 시스템** | 협업 필터링 + 콘텐츠 기반 | poe.ninja | ⭐⭐ |
| **메타 예측** | 시계열 + 패치노트 NLP | poe.ninja history | ⭐⭐⭐ |
| **아이템 가치 평가** | XGBoost 회귀 | Trade API | ⭐⭐ |
| **자동 레벨링 경로** | 강화학습 (PPO) | 게임 시뮬레이터 | ⭐⭐⭐⭐ |
| **스킬 젬 조합 최적화** | 조합론 + 휴리스틱 | PoB 계산기 | ⭐⭐⭐ |

### 8.2 데이터 수집 과제

- **공식 API 제한**: Rate limit, OAuth
- **게임 내 데이터**: ToS 위반 위험
- **과거 데이터**: poe.ninja가 유일한 장기 소스
- **빌드 표현**: 패시브 트리 + 장비 + 젬 통합 필요

### 8.3 평가 지표 제안

| 과제 | 지표 |
|------|------|
| 빌드 추천 | Precision@K, NDCG, 사용자 만족도 |
| 트리 최적화 | DPS, EHP, 투자 대비 효율 |
| 가격 예측 | MAPE, R², 실거래 검증 |
| 메타 예측 | 리그 시작 후 정확도 |

---

## 9. 참고 링크

### 9.1 학술 자료

| 유형 | 제목 | 링크 |
|------|------|------|
| 논문 | Tedious by Design (2022) | [ResearchGate](https://www.researchgate.net/publication/369437594) |
| 논문 | Aesthetics & MTX (DiGRA 2018) | [DiGRA](http://www.digra.org/digital-library/keywords/path-of-exile/) |
| 논문집 | Game Datasets (GitHub) | [leomaurodesenv/game-datasets](https://github.com/leomaurodesenv/game-datasets) |

### 9.2 기술 프로젝트

| 프로젝트 | 설명 | 링크 |
|----------|------|------|
| poeai | Deep Learning Bot | [GitHub](https://github.com/nogilnick/poeai) |
| poe-learning-layouts | Vision Transformer | [GitHub](https://github.com/kweimann/poe-learning-layouts) |
| PoESkillTree | 트리 플래너 + 최적화 | [GitHub](https://github.com/PoESkillTree/PoESkillTree) |
| RePoE | 게임 데이터 JSON | [GitHub](https://github.com/brather1ng/RePoE) |

### 9.3 공식 자료

| 자료 | 링크 |
|------|------|
| GDC Vault - Designing PoE | [GDC Vault](https://gdcvault.com/play/1026459/Designing-Path-of-Exile-to) |
| PoE Developer API | [Docs](https://www.pathofexile.com/developer/docs) |
| poe.ninja | [Website](https://poe.ninja) |

### 9.4 커뮤니티

| 플랫폼 | 용도 | 링크 |
|--------|------|------|
| r/pathofexile | 일반 토론 | [Reddit](https://reddit.com/r/pathofexile) |
| r/PathOfExileBuilds | 빌드 공유 | [Reddit](https://reddit.com/r/PathOfExileBuilds) |
| PoE Forum | 공식 포럼 | [Forum](https://www.pathofexile.com/forum) |

---

## 📝 변경 이력

| 날짜 | 버전 | 내용 |
|------|------|------|
| 2025-11-23 | 1.0 | 초안 작성 |

---

> **작성자 노트**: 이 문서는 PathcraftAI 개발 참고용으로 작성되었습니다.  
> PoE 관련 학술 연구는 매우 부족한 상태이므로, 새로운 연구 기회가 많습니다.
